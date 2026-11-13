<script setup lang="ts">
import { computed } from 'vue'

import { ACTION_META_BY_ID, cardImage } from '@/game/constants'
import { useGameStore } from '@/stores/game'

const game = useGameStore()

const card = computed(() => game.revealedCard)
const meta = computed(() => (card.value ? (ACTION_META_BY_ID[card.value.action] ?? null) : null))
const cardSrc = computed(() => (card.value ? cardImage(card.value.action, game.colorForPlayer(card.value.player_id)) : ''))
</script>

<template>
  <div v-if="card && meta" class="reveal">
    <p class="reveal__who">{{ card.player_name }} играет</p>
    <div class="reveal__card">
      <img class="reveal__img" :src="cardSrc" :alt="meta.label" />
    </div>
  </div>
</template>

<style scoped>
.reveal {
  position: fixed;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  pointer-events: none;
}

.reveal__who {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}

.reveal__card {
  width: 150px;
  aspect-ratio: 450 / 650;
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
  animation: reveal-in 0.25s ease;
}

.reveal__img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

@keyframes reveal-in {
  from { opacity: 0; transform: scale(0.7) rotate(-8deg); }
  to { opacity: 1; transform: scale(1) rotate(0deg); }
}
</style>