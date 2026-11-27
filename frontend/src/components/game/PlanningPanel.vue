<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { ACTION_META, COLOR_HEX, COLOR_NAMES, cardImage, type ActionMeta } from '@/game/constants'
import { useGameStore } from '@/stores/game'
import { useRoomStore } from '@/stores/room'

const SLOT_LABELS = ['Первое действие', 'Второе действие', 'Третье действие']

const game = useGameStore()
const room = useRoomStore()

const myColor = computed(() => (room.myPlayerId ? game.colorForPlayer(room.myPlayerId) : null))
const myColorLabel = computed(() => (myColor.value ? (COLOR_NAMES[myColor.value] ?? myColor.value) : ''))
const myColorHex = computed(() => (myColor.value ? (COLOR_HEX[myColor.value] ?? '#999') : '#999'))

function colorHex(color: string): string {
  return COLOR_HEX[color] ?? '#999'
}

function cardSrc(actionId: string): string {
  return cardImage(actionId, myColor.value ?? 'red')
}

const plan = ref<(string | null)[]>([null, null, null])
const submitted = ref(false)

const metaById: Record<string, ActionMeta> = Object.fromEntries(
  ACTION_META.map((a) => [a.id, a]),
)

const remaining = computed(() => ACTION_META.filter((a) => !plan.value.includes(a.id)))
const canSubmit = computed(() => plan.value.every((s) => s !== null) && !submitted.value)

function labelOf(id: string | null): string {
  return id ? (metaById[id]?.label ?? id) : ''
}

function iconOf(id: string | null): string {
  return id ? (metaById[id]?.icon ?? '') : ''
}

watch(
  () => game.phase,
  (p) => {
    if (p === 'planning') {
      plan.value = [null, null, null]
      submitted.value = false
    }
  },
)

function addToSlot(actionId: string) {
  if (submitted.value) return
  const idx = plan.value.indexOf(null)
  if (idx === -1) return
  plan.value[idx] = actionId
}

function clearSlot(index: number) {
  if (submitted.value) return
  plan.value[index] = null
}

function onDragStart(actionId: string, e: DragEvent) {
  if (submitted.value) return
  e.dataTransfer?.setData('text/plain', actionId)
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onDrop(index: number, e: DragEvent) {
  if (submitted.value) return
  const actionId = e.dataTransfer?.getData('text/plain')
  if (!actionId) return
  const next = [...plan.value]
  for (let i = 0; i < next.length; i++) {
    if (i !== index && next[i] === actionId) next[i] = null
  }
  next[index] = actionId
  plan.value = next
}

function submit() {
  if (!canSubmit.value) return
  game.submitPlan(plan.value as string[])
  submitted.value = true
}

function angleOf(index: number, total: number): number {
  return (index - (total - 1) / 2) * 6
}
</script>

<template>
  <div class="planning">
    <aside class="planning__players">
      <div class="planning__players-title">Порядок хода</div>
      <ol class="planning__players-list">
        <li
          v-for="p in game.turnOrder"
          :key="p.player_id"
          class="planning__player"
          :class="{ 'planning__player--you': p.player_id === room.myPlayerId }"
        >
          <span class="planning__player-dot" :style="{ background: colorHex(p.color) }"></span>
          <span class="planning__player-name">{{ p.name }}</span>
        </li>
      </ol>
    </aside>

    <div class="planning__cards">
      <div class="planning__slots">
      <div
        v-for="(slot, i) in plan"
        :key="i"
        class="slot"
        :class="{ 'slot--filled': slot }"
        :title="SLOT_LABELS[i]"
        @dragover.prevent
        @drop="onDrop(i, $event)"
        @click="clearSlot(i)"
      >
        <span class="slot__index">{{ SLOT_LABELS[i] }}</span>
        <img v-if="slot" class="slot__img" :src="cardSrc(slot)" :alt="labelOf(slot)" />
        <span v-else class="slot__hint">Перетащите карту</span>
      </div>
    </div>

    <div class="planning__hand">
      <button
        v-for="(a, i) in remaining"
        :key="a.id"
        class="card"
        type="button"
        :style="{ transform: `rotate(${angleOf(i, remaining.length)}deg)` }"
        draggable="true"
        @dragstart="onDragStart(a.id, $event)"
        @click="addToSlot(a.id)"
      >
        <img class="card__img" :src="cardSrc(a.id)" :alt="a.label" />
      </button>
    </div>
    </div>

    <div class="planning__info">
      <h2 class="planning__title">Выберите 3 действия по порядку</h2>
      <p v-if="myColorLabel" class="planning__me">
        <span class="planning__me-dot" :style="{ background: myColorHex }"></span>
        Вы — {{ myColorLabel }}
      </p>
      <p class="planning__timer">Осталось: {{ game.remainingSeconds }} с</p>

      <button
        v-if="!submitted"
        class="planning__submit"
        type="button"
        :disabled="!canSubmit"
        @click="submit"
      >
        Подтвердить
      </button>
      <p v-else class="planning__wait">Ожидание других игроков…</p>
    </div>
  </div>
</template>

<style scoped>
.planning {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  height: calc(100vh - 500px);
  height: calc(100dvh - 500px);
  display: grid;
  grid-template-columns: auto 1fr auto;
  grid-template-areas: "players cards info";
  align-items: center;
  gap: clamp(0.8rem, 2.5vh, 1.8rem);
  padding: clamp(0.6rem, 2vh, 1.4rem) clamp(0.9rem, 2vw, 1.5rem) clamp(0.7rem, 2.2vh, 1.6rem);
  color: #f2f2f2;
}

.planning__players {
  grid-area: players;
  width: 220px;
  padding-right: 1rem;
  border-right: 1px solid rgba(255, 255, 255, 0.15);
  align-self: center;
}

.planning__players-title {
  margin: 0 0 0.45rem;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  opacity: 0.7;
}

.planning__players-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: clamp(0.4rem, 1.4vh, 0.9rem);
}

.planning__player {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.9rem;
}

.planning__player--you {
  font-weight: 700;
  color: #ffd84d;
}

.planning__player-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.3);
  flex: 0 0 auto;
}

.planning__player-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.planning__cards {
  grid-area: cards;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: clamp(0.6rem, 3.5vh, 2.2rem);
}

.planning__info {
  grid-area: info;
  width: 220px;
  padding-left: 1rem;
  border-left: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: clamp(0.55rem, 2.2vh, 1.4rem);
}

.planning__title {
  margin: 0;
  font-size: 1.05rem;
}

.planning__timer {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #ffd84d;
}

.planning__me {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.planning__me-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.3);
}

.planning__slots {
  display: flex;
  gap: 0.7rem;
}

.slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  width: clamp(92px, 12vh, 116px);
  min-height: clamp(120px, 16.5vh, 158px);
  padding: 0.4rem;
  border: 2px dashed rgba(255, 255, 255, 0.35);
  border-radius: 10px;
  cursor: pointer;
}

.slot--filled {
  border-style: solid;
  border-color: #e6b23a;
  background: rgba(230, 178, 58, 0.14);
}

.slot__index {
  font-size: 0.66rem;
  text-transform: uppercase;
  opacity: 0.7;
}

.slot__img {
  width: clamp(68px, 8.5vh, 84px);
  aspect-ratio: 450 / 650;
  object-fit: cover;
  border-radius: 8px;
}
.slot__hint { font-size: 0.64rem; opacity: 0.5; }

.planning__hand {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  min-height: clamp(96px, 16vh, 132px);
  padding: 0 1rem;
}

.card {
  display: block;
  width: clamp(96px, 13vh, 126px);
  /* Ограничиваем ширину (и высоту) карты доступной высотой панели,
     чтобы карты не уходили под низ вьюпорта. */
  width: min(clamp(96px, 13vh, 126px), calc((76dvh - 500px) * 450 / 650));
  aspect-ratio: 450 / 650;
  margin: 0 -8px;
  padding: 0;
  /* border: 1px solid #b8c6d0; */
  border-radius: 10px;
  /* background: #fff; */
  overflow: hidden;
  cursor: grab;
  transform-origin: bottom center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  transition: box-shadow 0.15s ease;
}

.card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
  z-index: 1;
}

.card:active { cursor: grabbing; }

.card__img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.planning__submit {
  padding: 0.6rem 1.7rem;
  border: none;
  border-radius: 8px;
  background: #c0392b;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.planning__submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.planning__wait {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.85;
}

/* Высокие экраны: две колонки + крупнее карты. */
@media (max-height: 960px) {
  .planning__info {
    flex-direction: column;
  }
}

@media (min-height: 960px) {
  .planning {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      "players info"
      "players cards";
  }

  .planning__info {
    width: auto;
    justify-content: center;
    align-items: center;
    gap: clamp(0.6rem, 2vh, 1.2rem);
    border-left: none;
    padding-left: 0;
  }
}

@media (min-height: 1200px) {
  .card {
    width: clamp(96px, 13vh, 150px);
  }
}

@media (min-height: 1100px) {
  .planning__info {
    flex-direction: row;
  }
}

@media (min-height: 1200px) {
  .planning__info {
    flex-direction: column;
  }
}
</style>