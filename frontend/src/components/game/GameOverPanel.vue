<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useGameStore } from '@/stores/game'
import { useRoomStore } from '@/stores/room'

const router = useRouter()
const game = useGameStore()
const room = useRoomStore()

const winner = computed(() => {
  if (!game.winnerId) return null
  return game.bandits.find((b) => b.player_id === game.winnerId) ?? null
})

const ranked = computed(() => [...game.bandits].sort((a, b) => b.money - a.money))

function onExit() {
  room.leaveRoom()
  game.reset()
  router.push('/')
}
</script>

<template>
  <div class="gameover">
    <div class="gameover__card">
      <h2 class="gameover__title">Игра окончена</h2>

      <p v-if="winner" class="gameover__winner">
        Победитель: <strong>{{ winner.name }}</strong>
      </p>
      <p v-else class="gameover__winner">Ничья</p>

      <ul class="gameover__players">
        <li
          v-for="b in ranked"
          :key="b.player_id"
          class="gameover__player"
          :class="{ 'gameover__player--eliminated': b.eliminated }"
        >
          <span class="gameover__name">{{ b.name }}</span>
          <span class="gameover__money">${{ b.money }}</span>
          <span v-if="b.eliminated" class="gameover__status">выбыл</span>
          <span v-else-if="b.player_id === game.winnerId" class="gameover__status gameover__status--win">🏆</span>
        </li>
      </ul>

      <button class="gameover__button" type="button" @click="onExit">В меню</button>
    </div>
  </div>
</template>

<style scoped>
.gameover {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 14, 18, 0.7);
}

.gameover__card {
  width: 320px;
  padding: 1.4rem;
  border-radius: 14px;
  background: #fff;
  color: #1a2530;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
}

.gameover__title {
  margin: 0 0 0.5rem;
  text-align: center;
  font-size: 1.3rem;
}

.gameover__winner {
  margin: 0 0 0.8rem;
  text-align: center;
  font-size: 1rem;
}

.gameover__players {
  margin: 0;
  padding: 0;
  list-style: none;
}

.gameover__player {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid #e0e6ea;
}

.gameover__player--eliminated {
  opacity: 0.45;
}

.gameover__name {
  flex: 1;
}

.gameover__money {
  font-weight: 600;
}

.gameover__status {
  font-size: 0.8rem;
  color: #c0392b;
}

.gameover__status--win {
  color: inherit;
}

.gameover__button {
  margin-top: 1rem;
  width: 100%;
  padding: 0.6rem;
  border: none;
  border-radius: 8px;
  background: #c0392b;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}
</style>