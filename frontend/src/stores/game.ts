import { computed, nextTick, ref, watch } from 'vue'
import { defineStore } from 'pinia'

import { CAR_WIDTH, COLOR_NAMES, INSIDE_BOTTOM, LAYING_WIDTH, LOCOMOTIVE_INDEX, PLAYER_COLORS, ROOF_BOTTOM, STANDING_WIDTH } from '@/game/constants'
import { playCard, playDetach, playHorse, playMove, playShot, playTurn } from '@/game/sound'
import { sleep, useAnimationStore } from './animations'
import { useConnectionStore } from './connection'

export interface TrainCar {
  kind: 'delorean' | 'locomotive' | 'wagon'
  value: number | null
}

export interface BanditState {
  player_id: string
  name: string
  car_index: number
  level: 'inside' | 'roof'
  lane: number
  direction: 'toward_locomotive' | 'toward_tail'
  posture: 'standing' | 'prone'
  eliminated: boolean
  off_train: boolean
  money: number
}

export interface GameEventMessage {
  type: string
  round_number: number
  player_id?: string
  [key: string]: unknown
}

export interface RevealedCard {
  player_id: string
  player_name: string
  action: string
}

export interface BanditVisual {
  stateClass?: string
  left?: number
  bottom?: number
  opacity?: number
  mirror?: boolean
  walkFast?: boolean
}

export interface RoundResultEntry {
  name: string
  color: string
  colorName: string
}

export interface RoundResultData {
  eliminated: RoundResultEntry[]
  reward: RoundResultEntry | null
}

export interface BulletFlight {
  fromLeft: number
  fromBottom: number
  dx: number
  dy: number
}

export interface HorseRide {
  color: string
}

const GAME_EVENT_TYPES = [
  'planning_timed_out',
  'robbery_started',
  'round_started',
  'action_started',
  'turned_around',
  'moved',
  'changed_level',
  'shoot',
  'knocked',
  'horse',
  'stood_up',
  'lay_down',
  'delorean_entered',
  'moved_off_train',
  'knocked_off_train',
  'eliminated',
  'wagon_detached',
  'money_awarded',
  'game_finished',
  'time_paradox',
]

export const useGameStore = defineStore('game', () => {
  const connection = useConnectionStore()
  const animations = useAnimationStore()

  const train = ref<TrainCar[]>([])
  const bandits = ref<BanditState[]>([])
  const phase = ref<string | null>(null)
  const roundNumber = ref(1)
  const money = ref<Record<string, number>>({})
  const winnerId = ref<string | null>(null)
  const firstPlayerId = ref<string | null>(null)

  // Камера (прокрутка поезда) + раскрытая карта.
  const progress = ref(0.5)
  const viewportWidth = ref(0)
  const revealedCard = ref<RevealedCard | null>(null)
  const banditVisuals = ref<Record<string, BanditVisual>>({})
  const bullet = ref<BulletFlight | null>(null)
  const horseRide = ref<HorseRide | null>(null)
  const detachingWagon = ref(false)
  const deloreanFlash = ref(false)
  const planningTimeoutSeconds = ref(60)
  const planningDeadline = ref(0)
  const remainingSeconds = ref(60)
  const remainingCards = ref(0)
  const roundEliminatedIds = ref<string[]>([])
  const roundRewardId = ref<string | null>(null)
  const roundResult = ref<RoundResultData | null>(null)
  let roundResultResolve: (() => void) | null = null

  function banditById(pid: string): BanditState | undefined {
    return bandits.value.find((b) => b.player_id === pid)
  }

  function colorForPlayer(pid: string): string {
    const idx = bandits.value.findIndex((b) => b.player_id === pid)
    return PLAYER_COLORS[idx % PLAYER_COLORS.length] ?? 'red'
  }

  function colorNameFor(pid: string): string {
    const c = colorForPlayer(pid)
    return COLOR_NAMES[c] ?? c
  }

  const turnOrder = computed(() => {
    const list = bandits.value.filter((b) => !b.eliminated)
    if (list.length === 0) return []
    const startId = firstPlayerId.value
    const idx = startId ? list.findIndex((b) => b.player_id === startId) : 0
    const from = idx >= 0 ? idx : 0
    const ordered = [...list.slice(from), ...list.slice(0, from)]
    return ordered.map((b) => ({
      player_id: b.player_id,
      name: b.name,
      color: colorForPlayer(b.player_id),
      colorName: colorNameFor(b.player_id),
    }))
  })

  async function showRoundResult(): Promise<void> {
    const eliminated = roundEliminatedIds.value.map((pid) => {
      const b = banditById(pid)
      return { name: b?.name ?? pid, color: colorForPlayer(pid), colorName: colorNameFor(pid) }
    })
    const rid = roundRewardId.value
    const reward = rid
      ? { name: banditById(rid)?.name ?? rid, color: colorForPlayer(rid), colorName: colorNameFor(rid) }
      : null
    if (eliminated.length > 0 || reward) {
      roundResult.value = { eliminated, reward }
      await new Promise<void>((resolve) => {
        roundResultResolve = resolve
      })
    }
    // Сообщаем серверу, что окошко результата закрыто (или его не было).
    connection.send('confirm_round')
  }

  function dismissRoundResult() {
    roundResult.value = null
    if (roundResultResolve) {
      roundResultResolve()
      roundResultResolve = null
    }
  }

  function setState(state: Record<string, unknown>) {
    train.value = (state.train as TrainCar[]) ?? []
    bandits.value = (state.bandits as BanditState[]) ?? []
    phase.value = (state.phase as string) ?? null
    roundNumber.value = Number(state.round_number ?? 1)
    winnerId.value = (state.winner_id as string | null) ?? null
    firstPlayerId.value = (state.first_player_id as string | null) ?? null

    const nextMoney: Record<string, number> = {}
    for (const b of bandits.value) {
      nextMoney[b.player_id] = b.money
    }
    money.value = nextMoney
  }

  function reset() {
    train.value = []
    bandits.value = []
    phase.value = null
    roundNumber.value = 1
    money.value = {}
    winnerId.value = null
    firstPlayerId.value = null
    progress.value = 0.5
    revealedCard.value = null
    planningDeadline.value = 0
  }

  function submitPlan(actions: string[]) {
    connection.send('submit_plan', { actions })
  }

  function patchBandit(pid: string, patch: Partial<BanditState>) {
    const b = banditById(pid)
    if (b) Object.assign(b, patch)
  }

  function applyShifted(event: GameEventMessage) {
    const shifted = event.shifted as Array<[string, number]> | undefined
    if (!shifted) return
    for (const [sid, sLane] of shifted) {
      patchBandit(String(sid), { lane: Number(sLane) })
    }
  }

  function setVisual(pid: string, visual: BanditVisual) {
    banditVisuals.value[pid] = visual
  }

  function clearVisual(pid: string) {
    delete banditVisuals.value[pid]
  }

  function fireBullet(fromLeft: number, fromBottom: number, dx: number, dy: number) {
    bullet.value = { fromLeft, fromBottom, dx, dy }
  }

  function clearBullet() {
    bullet.value = null
  }

  function setPlanningTimeout(seconds: number) {
    planningTimeoutSeconds.value = seconds
  }

  let countdownTimer: number | null = null

  function setPlanningDeadline(deadlineSeconds: number) {
    if (deadlineSeconds > 0) planningDeadline.value = deadlineSeconds * 1000
  }

  function startPlanningCountdown() {
    stopPlanningCountdown()
    if (planningDeadline.value <= Date.now()) {
      planningDeadline.value = Date.now() + planningTimeoutSeconds.value * 1000
    }
    remainingSeconds.value = Math.max(0, Math.ceil((planningDeadline.value - Date.now()) / 1000))
    countdownTimer = window.setInterval(() => {
      const remain = Math.max(0, Math.ceil((planningDeadline.value - Date.now()) / 1000))
      remainingSeconds.value = remain
      if (remain <= 0) stopPlanningCountdown()
    }, 250)
  }

  function stopPlanningCountdown() {
    if (countdownTimer !== null) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }

  watch(phase, (p) => {
    if (p === 'planning') startPlanningCountdown()
    else stopPlanningCountdown()
  })

  // --- Камера: прокрутка поезда ---

  function setViewportWidth(width: number) {
    viewportWidth.value = width
  }

  function setProgress(value: number) {
    progress.value = Math.min(1, Math.max(0, value))
  }

  function carLeftPx(carIndex: number): number {
    const wagonCount = train.value.filter((c) => c.kind === 'wagon').length
    return (wagonCount + 1 - carIndex) * CAR_WIDTH
  }

  function banditPixel(pid: string): { left: number; bottom: number } | null {
    const b = banditById(pid)
    if (!b) return null
    const carLeft = carLeftPx(b.car_index)
    const cell = bandits.value
      .filter((o) => !o.eliminated && !o.off_train && o.car_index === b.car_index && o.level === b.level)
      .sort((x, y) => x.lane - y.lane)
    const widths = cell.map((o) => (o.posture === 'prone' ? LAYING_WIDTH : STANDING_WIDTH))
    const totalWidth = widths.reduce((s, w) => s + w, 0)
    const gap = Math.max(0, (CAR_WIDTH - totalWidth) / (cell.length + 1))
    let x = gap
    for (let i = 0; i < cell.length; i++) {
      const w = widths[i]
      if (cell[i].player_id === pid) {
        return {
          left: Math.round(carLeft + x + w / 2),
          bottom: (b.level === 'roof' ? ROOF_BOTTOM : INSIDE_BOTTOM) + 39,
        }
      }
      x += w + gap
    }
    return {
      left: Math.round(carLeft + CAR_WIDTH / 2),
      bottom: (b.level === 'roof' ? ROOF_BOTTOM : INSIDE_BOTTOM) + 39,
    }
  }

  function progressForCar(carIndex: number): number {
    if (viewportWidth.value <= 0) return progress.value
    const wagonCount = train.value.filter((c) => c.kind === 'wagon').length
    const trainWidth = (wagonCount + 2) * CAR_WIDTH
    const carLeft = (wagonCount + 1 - carIndex) * CAR_WIDTH
    const carCenter = carLeft + CAR_WIDTH / 2
    const denom = viewportWidth.value - trainWidth
    if (denom === 0) return progress.value
    return (viewportWidth.value / 2 - carCenter) / denom
  }

  async function scrollToCar(carIndex: number, durationMs = 700): Promise<void> {
    const target = Math.min(1, Math.max(0, progressForCar(carIndex)))
    const from = progress.value
    if (Math.abs(target - from) < 0.0001) return
    const start = performance.now()
    const scroll = new Promise<void>((resolve) => {
      const frame = (now: number) => {
        const t = Math.min(1, (now - start) / durationMs)
        const eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
        progress.value = from + (target - from) * eased
        if (t < 1) {
          requestAnimationFrame(frame)
        } else {
          progress.value = target
          resolve()
        }
      }
      requestAnimationFrame(frame)
    })
    await Promise.race([scroll, sleep(durationMs + 300)])
  }

  // --- Применение события к состоянию ---

  function applyEvent(event: GameEventMessage) {
    const pid = String(event.player_id ?? '')
    switch (event.type) {
      case 'robbery_started':
        phase.value = 'robbery'
        remainingCards.value = bandits.value.filter((b) => !b.eliminated).length * 3
        roundEliminatedIds.value = []
        roundRewardId.value = null
        break
      case 'round_started':
        phase.value = 'planning'
        roundNumber.value = Number(event.round_number)
        firstPlayerId.value = event.first_player_id == null ? null : String(event.first_player_id)
        // Перезапуск таймера перед новым раундом.
        if (event.planning_deadline != null) {
          setPlanningDeadline(Number(event.planning_deadline))
        } else {
          planningDeadline.value = 0
        }
        break
      case 'turned_around':
        if (pid) patchBandit(pid, { direction: String(event.direction) as BanditState['direction'] })
        break
      case 'moved':
        if (pid) patchBandit(pid, {
          car_index: Number(event.to_car),
          level: String(event.level) as BanditState['level'],
          lane: Number(event.lane),
        })
        applyShifted(event)
        break
      case 'changed_level':
        if (pid) patchBandit(pid, {
          car_index: Number(event.car_index),
          level: String(event.level) as BanditState['level'],
          lane: Number(event.lane),
        })
        applyShifted(event)
        break
      case 'knocked':
        if (pid) patchBandit(pid, {
          car_index: Number(event.to_car),
          level: String(event.level) as BanditState['level'],
          lane: Number(event.lane),
          posture: 'prone',
        })
        applyShifted(event)
        break
      case 'horse':
        if (pid) patchBandit(pid, {
          car_index: Number(event.car_index),
          level: String(event.level) as BanditState['level'],
          lane: Number(event.lane),
          direction: String(event.direction) as BanditState['direction'],
          posture: 'standing',
          off_train: false,
        })
        applyShifted(event)
        break
      case 'stood_up':
        if (pid) patchBandit(pid, { posture: 'standing' })
        break
      case 'lay_down':
        if (pid) patchBandit(pid, { posture: 'prone' })
        break
      case 'delorean_entered':
        if (pid) patchBandit(pid, {
          car_index: Number(event.car_index),
          level: String(event.level) as BanditState['level'],
          lane: Number(event.lane),
          direction: String(event.direction) as BanditState['direction'],
          posture: 'standing',
          off_train: false,
        })
        applyShifted(event)
        // Перемотка Делориана: бандит переиграет свои карты заново.
        remainingCards.value = remainingCards.value + 2
        break
      case 'moved_off_train':
      case 'knocked_off_train':
        if (pid) patchBandit(pid, { off_train: true })
        break
      case 'eliminated':
        if (pid) {
          patchBandit(pid, { eliminated: true })
          if (!roundEliminatedIds.value.includes(pid)) roundEliminatedIds.value.push(pid)
        }
        break
      case 'wagon_detached':
        train.value = train.value.slice(0, -1)
        break
      case 'money_awarded': {
        const b = banditById(pid)
        if (b) {
          b.money += Number(event.amount)
          money.value[pid] = b.money
        }
        if (pid) roundRewardId.value = pid
        break
      }
      case 'game_finished':
        phase.value = 'finished'
        winnerId.value = event.winner_id == null ? null : String(event.winner_id)
        break
      default:
        break
    }
  }

  // --- Анимация события ---

  function animationForEvent(event: GameEventMessage): () => Promise<void> {
    if (event.type === 'action_started') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        revealedCard.value = {
          player_id: pid,
          player_name: b?.name ?? pid,
          action: String(event.action ?? ''),
        }
        remainingCards.value = Math.max(0, remainingCards.value - 1)
        await sleep(1100)
        if (b && !b.off_train && !b.eliminated) {
          await scrollToCar(b.car_index)
        }
        await sleep(300)
        revealedCard.value = null
      }
    }

    if (event.type === 'moved') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (b) {
          const side = b.direction === 'toward_locomotive' ? 'right' : 'left'
          setVisual(pid, { stateClass: `walking_${side}` })
          // Флашим DOM и фиксируем старое left через reflow, чтобы transition сработал.
          await nextTick()
          void document.body.offsetHeight
          applyEvent(event)
          await sleep(1600)
          clearVisual(pid)
        } else {
          applyEvent(event)
          await sleep(800)
        }
      }
    }

    if (event.type === 'changed_level') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (!b) {
          applyEvent(event)
          await sleep(800)
          return
        }
        const originalSide = b.direction === 'toward_locomotive' ? 'right' : 'left'
        const tailEdgeLeft = carLeftPx(b.car_index)
        const isClimbingUp = b.level === 'inside'

        // 1. Повернуться к хвосту (если ещё не).
        if (originalSide !== 'left') {
          setVisual(pid, { stateClass: 'cowboy_rotate' })
          await sleep(600)
        }
        setVisual(pid, { stateClass: 'staying_left' })
        await sleep(250)

        // 2. Дойти до хвостового края (ускоренно в 2 раза).
        setVisual(pid, { stateClass: 'walking_left', left: tailEdgeLeft, walkFast: true })
        await sleep(800)

        if (isClimbingUp) {
          // Вверх: развернуться к локомотиву (оставаясь у края), затем climbing.
          setVisual(pid, { stateClass: 'cowboy_rotate', left: tailEdgeLeft, mirror: true })
          await sleep(600)
          setVisual(pid, { stateClass: 'staying_right', left: tailEdgeLeft })
          await sleep(250)
          setVisual(pid, { stateClass: 'climbing', left: tailEdgeLeft })
          await sleep(2000)
          // Мгновенно на крышу (bottom) — спрайт уже показал подъём.
          setVisual(pid, { stateClass: 'teleporting', left: tailEdgeLeft, bottom: ROOF_BOTTOM })
          await sleep(50)
          // Если до подъёма смотрел к хвосту — вернуть взгляд к хвосту (состояние его не меняет).
          if (originalSide === 'left') {
            setVisual(pid, { stateClass: 'cowboy_rotate', left: tailEdgeLeft, bottom: ROOF_BOTTOM })
            await sleep(600)
            setVisual(pid, { stateClass: 'staying_left', left: tailEdgeLeft, bottom: ROOF_BOTTOM })
            await sleep(250)
          }
        } else {
          // Вниз: спуск (jumping_down), остаёмся лицом к хвосту, у края.
          setVisual(pid, { stateClass: 'jumping_down', left: tailEdgeLeft, bottom: INSIDE_BOTTOM })
          await sleep(2000)
          // Развернуться обратно к локомотиву — только если до спуска смотрел к локомотиву.
          if (originalSide !== 'left') {
            setVisual(pid, { stateClass: 'cowboy_rotate', left: tailEdgeLeft, bottom: INSIDE_BOTTOM, mirror: true })
            await sleep(600)
            setVisual(pid, { stateClass: 'staying_right', left: tailEdgeLeft, bottom: INSIDE_BOTTOM })
            await sleep(250)
          }
        }

        // 5. Применить состояние (lane 0, новый уровень) и снять override.
        applyEvent(event)
        clearVisual(pid)

        // 6. Равномерное распределение по новой ячейке.
        await sleep(400)
      }
    }

    if (event.type === 'turned_around') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (!b) {
          applyEvent(event)
          await sleep(800)
          return
        }
        // Развернуться: rotate-спрайт (зеркалим, если смотрел к хвосту).
        setVisual(pid, { stateClass: 'cowboy_rotate', mirror: b.direction === 'toward_tail' })
        await sleep(1000)
        applyEvent(event)
        clearVisual(pid)
        await sleep(200)
      }
    }

    if (event.type === 'shoot') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const shooter = banditById(pid)
        if (shooter) {
          const side = shooter.direction === 'toward_locomotive' ? 'right' : 'left'
          const shootClass = event.from_hip ? `shoot_from_hip_${side}` : `shoot_${side}`
          setVisual(pid, { stateClass: shootClass })
        }

        const from = shooter ? banditPixel(pid) : null
        const targetId = event.target_id ? String(event.target_id) : null
        const to = targetId ? banditPixel(targetId) : null

        // Выстрел (звук + пуля) — в середине спрайта (~1.0 с), а не в начале.
        await sleep(1000)
        playShot()
        if (from) {
          if (to) {
            fireBullet(from.left, from.bottom, to.left - from.left, to.bottom - from.bottom)
          } else if (shooter) {
            const dir = shooter.direction === 'toward_locomotive' ? 1 : -1
            fireBullet(from.left, from.bottom, dir * 600, 0)
          }
        }

        // Пуля долетает за 0.6 с.
        await sleep(600)
        clearBullet()

        // Фокус на цели, в которую попала пуля.
        if (targetId) {
          const target = banditById(targetId)
          if (target && !target.off_train && !target.eliminated) {
            await scrollToCar(target.car_index)
          }
        }

        // Спрайт выстрела доигрывает (суммарно 2 с).
        await sleep(400)

        if (shooter) clearVisual(pid)
      }
    }

    if (event.type === 'knocked') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (!b) {
          applyEvent(event)
          await sleep(800)
          return
        }
        const fromCar = Number(event.from_car)
        const toCar = Number(event.to_car)
        const facesHead = b.direction === 'toward_locomotive'
        const side = facesHead ? 'right' : 'left'
        const knockTowardHead = toCar < fromCar
        const fallClass = knockTowardHead === facesHead ? `fall_forvard_${side}` : `fall_back_${side}`

        setVisual(pid, { stateClass: fallClass })
        await sleep(1700)
        // Фиксируем позицию мгновенно, без лишнего слайда к целевому вагону.
        setVisual(pid, { stateClass: 'teleporting' })
        applyEvent(event)
        await sleep(30)
        clearVisual(pid)
      }
    }

    if (event.type === 'horse') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)

        // 1. Ковбой fade'ом исчезает.
        if (b) setVisual(pid, { opacity: 0 })
        await sleep(300)

        // 2. Лошадь едет независимо от поезда (как в example).
        horseRide.value = { color: colorForPlayer(pid) }
        // На 2/3 анимации фокусируемся на локомотиве.
        await sleep(3300)
        await scrollToCar(LOCOMOTIVE_INDEX)
        await sleep(1700)
        horseRide.value = null

        // 3. Ставим ковбоя на локомотив по правилам и fade'ом проявляем.
        applyEvent(event)
        if (b) {
          clearVisual(pid)
          await sleep(300)
        }
      }
    }

    if (event.type === 'stood_up') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (!b) {
          applyEvent(event)
          await sleep(800)
          return
        }
        const side = b.direction === 'toward_locomotive' ? 'right' : 'left'
        setVisual(pid, { stateClass: `getup_${side}` })
        applyEvent(event)
        await sleep(2000)
        clearVisual(pid)
      }
    }

    if (event.type === 'lay_down') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (!b) {
          applyEvent(event)
          await sleep(800)
          return
        }
        const side = b.direction === 'toward_locomotive' ? 'right' : 'left'
        setVisual(pid, { stateClass: `shoot_itself_${side}` })
        applyEvent(event)
        // Звук выстрела — чуть раньше середины спрайта (~1.7 с из 4 с).
        await sleep(1700)
        playShot()
        await sleep(2300)
        clearVisual(pid)
      }
    }

    if (event.type === 'eliminated') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (b) {
          setVisual(pid, { opacity: 0 })
          await sleep(500)
        }
        applyEvent(event)
        if (b) clearVisual(pid)
      }
    }

    if (event.type === 'wagon_detached') {
      return async () => {
        detachingWagon.value = true
        await sleep(1200)
        applyEvent(event)
        detachingWagon.value = false
        // Ждём, пока отцепленный вагон исчезнет из DOM (ширина поезда обновится),
        // иначе центрирование посчитается по старой ширине.
        await nextTick()
        // В конце раунда центрируем поезд (и движок .mover).
        setProgress(0.5)
        await showRoundResult()
      }
    }

    if (event.type === 'delorean_entered') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        const cause = event.cause === 'shoot' ? 'shoot' : 'move'

        // 1. Обычная анимация действия (вход/влёт в Делориан) + fade до завершения.
        if (b) {
          if (cause === 'shoot') {
            const facesHead = b.direction === 'toward_locomotive'
            const side = facesHead ? 'right' : 'left'
            const fallClass = facesHead ? `fall_forvard_${side}` : `fall_back_${side}`
            setVisual(pid, { stateClass: fallClass })
            await sleep(1000)
            setVisual(pid, { stateClass: fallClass, opacity: 0 })
            await sleep(700)
          } else {
            const dir = b.direction === 'toward_locomotive' ? 'right' : 'left'
            const targetLeft = carLeftPx(0) + CAR_WIDTH * 0.3
            setVisual(pid, { stateClass: `walking_${dir}`, left: targetLeft })
            await sleep(900)
            setVisual(pid, { stateClass: `walking_${dir}`, left: targetLeft, opacity: 0 })
            await sleep(700)
          }
        } else {
          await sleep(300)
        }

        // 2. Мгновенный телепорт + вспышка + фокус на последний вагон.
        if (b) setVisual(pid, { opacity: 0, stateClass: 'teleporting' })
        applyEvent(event)
        deloreanFlash.value = true

        // Фокус на последний вагон (одновременно со вспышкой).
        await scrollToCar(Number(event.car_index))

        // 3. Пауза «машины времени».
        await sleep(300)
        deloreanFlash.value = false

        // 4. Fade-in уже в хвосте.
        if (b) {
          clearVisual(pid)
          await sleep(300)
        }
      }
    }

    if (event.type === 'moved_off_train') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (b) {
          // Ковбой сбегает назад за левый край поезда.
          setVisual(pid, { stateClass: 'walking_left', left: -60 })
          await sleep(1000)
          setVisual(pid, { stateClass: 'walking_left', left: -60, opacity: 0 })
          await sleep(600)
          applyEvent(event)
          clearVisual(pid)
        } else {
          applyEvent(event)
          await sleep(800)
        }
      }
    }

    if (event.type === 'knocked_off_train') {
      return async () => {
        const pid = String(event.player_id ?? '')
        const b = banditById(pid)
        if (b) {
          const facesHead = b.direction === 'toward_locomotive'
          const side = facesHead ? 'right' : 'left'
          // Вылет за хвост выстрелом: отброс к хвосту.
          const fallClass = facesHead ? `fall_back_${side}` : `fall_forvard_${side}`
          setVisual(pid, { stateClass: fallClass })
          await sleep(1000)
          setVisual(pid, { stateClass: fallClass, opacity: 0 })
          await sleep(700)
          applyEvent(event)
          clearVisual(pid)
        } else {
          applyEvent(event)
          await sleep(800)
        }
      }
    }

    // Заглушка для остальных событий (реальные анимации — пункты 46-49).
    return async () => {
      applyEvent(event)
      await sleep(800)
    }
  }

  // --- Подписка на события ---

  function playSoundForEvent(event: GameEventMessage) {
    switch (event.type) {
      case 'action_started': playCard(); break
      case 'moved': playMove(); break
      case 'horse': playHorse(); break
      case 'wagon_detached': playDetach(); break
      case 'turned_around': playTurn(); break
      default: break
    }
  }

  function setupListeners() {
    for (const type of GAME_EVENT_TYPES) {
      connection.on(type, (message) => {
        const event = message as unknown as GameEventMessage
        animations.enqueue(async () => {
          playSoundForEvent(event)
          await animationForEvent(event)()
        })
      })
    }
  }

  return {
    train, bandits, phase, roundNumber, money, winnerId,
    progress, viewportWidth, revealedCard,
    banditById, setState, reset, applyEvent, submitPlan, setupListeners,
    setViewportWidth, setProgress, scrollToCar, carLeftPx, setVisual, clearVisual, colorForPlayer,
    bullet, fireBullet, clearBullet, horseRide, detachingWagon, remainingCards, deloreanFlash,
    planningTimeoutSeconds, remainingSeconds, setPlanningTimeout, setPlanningDeadline, firstPlayerId, turnOrder,
    banditVisuals, roundResult, dismissRoundResult, colorNameFor,
  }
})