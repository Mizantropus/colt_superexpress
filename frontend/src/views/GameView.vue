<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import CardReveal from '@/components/game/CardReveal.vue'
import GameOverPanel from '@/components/game/GameOverPanel.vue'
import MusicPlayer from '@/components/game/MusicPlayer.vue'
import PixelClouds from '@/components/game/PixelClouds.vue'
import PlanningPanel from '@/components/game/PlanningPanel.vue'
import RoundResultPopup from '@/components/game/RoundResultPopup.vue'
import { CAR_WIDTH, INSIDE_BOTTOM, LAYING_WIDTH, PLAYER_COLORS, ROOF_BOTTOM, STANDING_WIDTH } from '@/game/constants'
import { useGameStore, type BanditState } from '@/stores/game'
import { useRoomStore } from '@/stores/room'

const viewport = ref<HTMLDivElement | null>(null)
const track = ref<HTMLDivElement | null>(null)
const mover = ref<HTMLDivElement | null>(null)
const train = ref<HTMLDivElement | null>(null)
const cowboys = ref<HTMLDivElement | null>(null)

const gameStore = useGameStore()
const room = useRoomStore()
const router = useRouter()

function leaveGame() {
  // После завершения партии сервер уже сбросил членство — просто уходим.
  if (gameStore.phase !== 'finished') {
    room.leaveRoom()
  }
  router.push('/')
}

// Масштаб всей игры — аналог зума браузера (Ctrl + колесо):
// мультипликативный шаг, диапазон от -50% до +50%.
const scale = ref(1)
const scaleOpen = ref(false)
const SCALE_FACTOR = 1.05
const SCALE_MIN = 0.5
const SCALE_MAX = 1.5

const canZoomIn = computed(() => scale.value < SCALE_MAX - 1e-6)
const canZoomOut = computed(() => scale.value > SCALE_MIN + 1e-6)

function zoomIn() {
  if (canZoomIn.value) scale.value = Math.min(SCALE_MAX, +(scale.value * SCALE_FACTOR).toFixed(4))
}

function zoomOut() {
  if (canZoomOut.value) scale.value = Math.max(SCALE_MIN, +(scale.value / SCALE_FACTOR).toFixed(4))
}

// Применяем масштаб ко всей странице (аналог зума браузера).
watch(scale, (v) => {
  document.documentElement.style.zoom = String(v)
  // После рефлоу пересчитываем JS-замеры (clientWidth/offsetWidth изменились).
  requestAnimationFrame(() => {
    if (viewport.value) {
      gameStore.setViewportWidth(viewport.value.clientWidth)
      updatePositions()
    }
  })
}, { immediate: true })

const myMoney = computed(() => (room.myPlayerId ? (gameStore.money[room.myPlayerId] ?? 0) : 0))

const wagonsReversed = computed(() =>
  gameStore.train.filter((car) => car.kind === 'wagon').reverse(),
)

interface RenderedBandit {
  player_id: string
  color: string
  stateClass: string
  left: number
  bottom: number
  mirror: boolean
  walkFast: boolean
}

// Бандиты: равномерная раскладка по ячейкам (вагон+уровень), сортировка по lane.
const renderedBandits = computed<RenderedBandit[]>(() => {
  const wagonCount = gameStore.train.filter((car) => car.kind === 'wagon').length
  const active = gameStore.bandits.filter((b) => !b.eliminated && !b.off_train)

  const colorByPlayer = new Map<string, string>()
  gameStore.bandits.forEach((b, i) => {
    colorByPlayer.set(b.player_id, PLAYER_COLORS[i % PLAYER_COLORS.length] ?? 'red')
  })

  const cells = new Map<string, BanditState[]>()
  for (const b of active) {
    const key = `${b.car_index}:${b.level}`
    if (!cells.has(key)) cells.set(key, [])
    cells.get(key)!.push(b)
  }

  const result: RenderedBandit[] = []
  for (const [, cell] of cells) {
    cell.sort((a, b) => a.lane - b.lane)
    const widths = cell.map((b) => (b.posture === 'prone' ? LAYING_WIDTH : STANDING_WIDTH))
    const totalWidth = widths.reduce((s, w) => s + w, 0)
    const gap = Math.max(0, (CAR_WIDTH - totalWidth) / (cell.length + 1))
    const carLeft = (wagonCount + 1 - cell[0].car_index) * CAR_WIDTH
    let x = gap
    cell.forEach((b, i) => {
      const side = b.direction === 'toward_locomotive' ? 'right' : 'left'
      const baseState = b.posture === 'prone' ? `laying_${side}` : `staying_${side}`
      const visual = gameStore.banditVisuals[b.player_id]
      const stateClass = visual?.stateClass ?? baseState
      const left = visual?.left ?? Math.round(carLeft + x)
      const bottom = visual?.bottom ?? (b.level === 'roof' ? ROOF_BOTTOM : INSIDE_BOTTOM)
      const opacity = visual?.opacity ?? 1
      result.push({
        player_id: b.player_id,
        color: colorByPlayer.get(b.player_id) ?? 'red',
        stateClass,
        left,
        bottom,
        opacity,
        mirror: visual?.mirror ?? false,
        walkFast: visual?.walkFast ?? false,
      })
      x += widths[i] + gap
    })
  }
  return result
})

let dragOffset = 0
let dragging = false

function updatePositions() {
  if (!viewport.value || !track.value || !mover.value || !train.value) return
  const trackWidth = track.value.clientWidth
  const moverRadius = mover.value.offsetWidth / 2
  const minCenter = Math.min(moverRadius, trackWidth / 2)
  const maxCenter = Math.max(minCenter, trackWidth - moverRadius)
  const center = minCenter + (maxCenter - minCenter) * gameStore.progress
  const trainOffset = (viewport.value.clientWidth - train.value.offsetWidth) * gameStore.progress

  mover.value.style.left = `${center}px`
  train.value.style.left = `${trainOffset}px`
  if (cowboys.value) {
    cowboys.value.style.left = `${trainOffset}px`
    cowboys.value.style.width = `${train.value.offsetWidth}px`
  }
  mover.value.setAttribute('aria-valuenow', String(Math.round(gameStore.progress * 100)))
}

function setProgressFromPointer(clientX: number) {
  if (!track.value || !mover.value) return
  const trackLeft = track.value.getBoundingClientRect().left
  const trackWidth = track.value.clientWidth
  const moverRadius = mover.value.offsetWidth / 2
  const minCenter = Math.min(moverRadius, trackWidth / 2)
  const maxCenter = Math.max(minCenter, trackWidth - moverRadius)
  const center = Math.min(maxCenter, Math.max(minCenter, clientX - trackLeft - dragOffset))
  gameStore.setProgress(maxCenter === minCenter ? 0.5 : (center - minCenter) / (maxCenter - minCenter))
  updatePositions()
}

function onPointerDown(event: PointerEvent) {
  if (!mover.value) return
  dragging = true
  dragOffset = event.clientX - mover.value.getBoundingClientRect().left - mover.value.offsetWidth / 2
  mover.value.setPointerCapture(event.pointerId)
  event.preventDefault()
}

function onPointerMove(event: PointerEvent) {
  if (dragging) setProgressFromPointer(event.clientX)
}

function stopDragging() {
  dragging = false
}

function onKeydown(event: KeyboardEvent) {
  let next = gameStore.progress
  if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') next -= 0.02
  else if (event.key === 'ArrowRight' || event.key === 'ArrowUp') next += 0.02
  else if (event.key === 'PageDown') next -= 0.1
  else if (event.key === 'PageUp') next += 0.1
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = 1
  else return
  event.preventDefault()
  gameStore.setProgress(next)
  updatePositions()
}

function onResize() {
  gameStore.setViewportWidth(viewport.value?.clientWidth ?? 0)
  updatePositions()
}

watch(() => gameStore.progress, () => updatePositions())

onMounted(() => {
  gameStore.setViewportWidth(viewport.value?.clientWidth ?? 0)
  updatePositions()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  document.documentElement.style.zoom = ''
})
</script>

<template>
  <div class="game">
    <MusicPlayer />
    <PlanningPanel v-if="gameStore.phase === 'planning'" />
    <GameOverPanel v-if="gameStore.phase === 'finished'" />
    <RoundResultPopup />
    <div v-if="gameStore.deloreanFlash" class="delorean-flash" />
    <CardReveal />

    <div v-if="gameStore.phase === 'robbery'" class="deck">
      <div class="deck__cards">
        <div class="deck__card deck__card--b1" />
        <div class="deck__card deck__card--b2" />
        <div class="deck__card deck__card--top" />
      </div>
      <p class="deck__count">Осталось карт: {{ gameStore.remainingCards }}</p>
    </div>

    <div class="wallet">
      <span class="wallet__label">Ваши деньги</span>
      <span class="wallet__amount">{{ myMoney }}$</span>
    </div>

    <div ref="viewport" class="background_wrapper">
      <div class="background">
        <!-- <img src="/images/mountains.png" alt="" />
        <img src="/images/mountains.png" alt="" />
        <img src="/images/mountains.png" alt="" />
        <img src="/images/mountains.png" alt="" /> -->
      </div>

      <PixelClouds />

      <div class="reels"></div>

      <div ref="train" class="train_wrapper">
        <div
          v-for="(car, i) in wagonsReversed"
          :key="i"
          class="vagon"
          :class="{ 'vagon--detaching': gameStore.detachingWagon && i === 0 }"
        >
          <div class="vagon_wheel wheel_1" />
          <div class="vagon_wheel wheel_2" />
          <div class="vagon_wheel wheel_3" />
          <div class="vagon_wheel wheel_4" />
        </div>
        <div class="lokomotive">
          <div class="vagon_wheel wheel_3" />
          <div class="vagon_wheel wheel_4" />
          <div class="wheel" />
        </div>
        <div class="delorian">
          <div class="wheel_front" />
          <div class="wheel_back" />
          <div class="small_wheel" />
        </div>
      </div>

      <div ref="cowboys" class="cowboys_wrapper">
        <div
          v-for="b in renderedBandits"
          :key="b.player_id"
          class="cowboy"
          :class="[b.color, b.stateClass, b.mirror ? 'cowboy--mirror' : '', b.walkFast ? 'walk-fast' : '']"
          :style="{ left: `${b.left}px`, bottom: `${b.bottom}px`, position: 'absolute', opacity: b.opacity }"
        />

        <div
          v-if="gameStore.bullet"
          class="bullet"
          :style="{
            '--from-left': `${gameStore.bullet.fromLeft}px`,
            '--from-bottom': `${gameStore.bullet.fromBottom}px`,
            '--dx': `${gameStore.bullet.dx}px`,
            '--dy': `${gameStore.bullet.dy}px`,
          }"
        />
      </div>

      <div class="hobby_horsing_wrapper">
        <div
          v-if="gameStore.horseRide"
          class="hobby_horsing"
          :class="`horsing_${gameStore.horseRide.color}`"
        />
      </div>
    </div>

    <div ref="track" class="mover_wrapper">
      <div
        ref="mover"
        class="mover"
        role="slider"
        tabindex="0"
        aria-label="Положение поезда"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow="50"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="stopDragging"
        @pointercancel="stopDragging"
        @keydown="onKeydown"
      />
    </div>

    <div class="ornament"></div>

    <button class="leave-game" type="button" @click="leaveGame">Покинуть игру</button>

  </div>

  <div class="scale-control" :style="{ zoom: 1 / scale }">
    <button class="scale-control__toggle" type="button" @click="scaleOpen = !scaleOpen">🔍</button>
    <div class="scale-control__zoom" :class="{ 'scale-control__zoom--open': scaleOpen }">
      <button class="scale-control__btn" type="button" :disabled="!canZoomIn" @click="zoomIn">+</button>
      <button class="scale-control__btn" type="button" :disabled="!canZoomOut" @click="zoomOut">−</button>
    </div>
  </div>
</template>

<style scoped>
.game {
  width: 100%;
  height: 100%;
}

.scale-control {
  position: fixed;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
}

.scale-control__toggle {
  position: relative;
  z-index: 2;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 1.15rem;
  cursor: pointer;
  backdrop-filter: blur(2px);
}

.scale-control__zoom {
  position: absolute;
  right: 52px;
  top: 0;
  display: flex;
  gap: 6px;
  opacity: 0;
  transform: translateX(52px);
  pointer-events: none;
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.scale-control__zoom--open {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.scale-control__btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  backdrop-filter: blur(2px);
}

.scale-control__btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.leave-game {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 60;
  padding: 0.5rem 1.1rem;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
}

.leave-game:hover {
  background: rgba(0, 0, 0, 0.75);
}

.cowboy {
  transition: left 0.4s ease, bottom 0.4s ease, opacity 0.3s ease;
}

/* Убираем демо-анимацию cowboy-move из example и задаём темп ходьбы. */
.cowboy.walking_right,
.cowboy.walking_left {
  animation: none;
  transition: left 1.6s linear;
}

/* Быстрый подход к краю вагона (изменить уровень) — в 2 раза быстрее. */
.cowboy.walk-fast {
  transition: left 0.8s linear !important;
}
.cowboy.walk-fast::before {
  animation-duration: 0.8s !important;
}

/* Темп подъёма/спуска по уровню. */
.cowboy.climbing {
  transition: bottom 2s ease, left 0.4s ease;
}

/* Спуск: вертикаль ведёт спрайт, позиция меняется без перехода. */
.cowboy.jumping_down {
  transition: none !important;
}

/* Убираем демо-позиционную анимацию падения. */
.cowboy.fall_forvard_right,
.cowboy.fall_forvard_left,
.cowboy.fall_back_right,
.cowboy.fall_back_left {
  animation: none;
}

/* Убираем демо-сдвиг из example (лежащий ковбой был смещён на -390px). */
.cowboy.laying_right {
  transform: none !important;
}

/* Телепорт в Делориан: позиция меняется мгновенно, без плавного перехода. */
.cowboy.teleporting {
  transition: none !important;
}

/* Зеркалирование по горизонтали (для разворотов из положения «лицом к хвосту»). */
.cowboy--mirror {
  transform: scaleX(-1);
}

/* Сцена не выделяется текстом: пустые content:'' не дают каретку/курсор. */
.background_wrapper {
  user-select: none;
}

/* Вспышка при телепорте в Делориан. */
.delorean-flash {
  position: fixed;
  inset: 0;
  z-index: 45;
  pointer-events: none;
  background: radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.95), rgba(140, 200, 255, 0.55));
  animation: delorean-flash 0.3s ease-out forwards;
}

@keyframes delorean-flash {
  0% { opacity: 0; }
  40% { opacity: 1; }
  100% { opacity: 0; }
}

/* Отцепление вагона: съезжает вниз-влево и исчезает. */
.vagon--detaching {
  animation: wagon-detach 1.2s ease-in forwards;
}

@keyframes wagon-detach {
  to {
    transform: translateX(-390px) translateY(60px);
    opacity: 0;
  }
}

/* Пуля. */
.bullet {
  position: absolute;
  left: var(--from-left);
  bottom: var(--from-bottom);
  width: 10px;
  height: 6px;
  border-radius: 3px;
  background: #ffd84d;
  box-shadow: 0 0 6px #ffd84d;
  pointer-events: none;
  animation: bullet-fly 0.6s ease-out forwards;
}

@keyframes bullet-fly {
  to {
    transform: translate(var(--dx), var(--dy));
  }
}



/* Стопка оставшихся карт. */
.deck {
  position: fixed;
  left: 50%;
  top: 12px;
  transform: translateX(-50%);
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 10px;
  pointer-events: none;
}

.deck__cards {
  position: relative;
  width: 34px;
  height: 46px;
}

.deck__card {
  position: absolute;
  left: 0;
  top: 0;
  width: 34px;
  height: 46px;
  border-radius: 5px;
  border: 1px solid #8b5a2b;
  background: #f4f1ea;
}

.deck__card--b1 { transform: translate(-5px, -5px); }
.deck__card--b2 { transform: translate(-2px, -2px); }
.deck__card--top { box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45); }

.deck__count {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
}

.wallet {
  position: fixed;
  left: 18px;
  top: 18px;
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  pointer-events: none;
}

.wallet__label {
  font-size: 0.8rem;
  opacity: 0.85;
}

.wallet__amount {
  font-size: 1.15rem;
  font-weight: 700;
  color: #ffd84d;
}
</style>