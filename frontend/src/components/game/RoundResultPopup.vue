<script setup lang="ts">
import { computed } from 'vue'

import { COLOR_HEX } from '@/game/constants'
import { useGameStore } from '@/stores/game'

const game = useGameStore()

const result = computed(() => game.roundResult)
</script>

<template>
  <div v-if="result" class="round-result">
    <div class="round-result__panel">
      <h2 class="round-result__title">Итоги раунда</h2>

      <ul class="round-result__list">
        <li v-for="e in result.eliminated" :key="e.name" class="round-result__item">
          <span class="dot" :style="{ background: COLOR_HEX[e.color] ?? '#999' }"></span>
          <span>Игрок {{ e.name }} ({{ e.colorName }}) выбыл</span>
        </li>
        <li v-if="result.reward" class="round-result__item round-result__item--reward">
          <span class="dot" :style="{ background: COLOR_HEX[result.reward.color] ?? '#999' }"></span>
          <span>Игрок {{ result.reward.name }} ({{ result.reward.colorName }}) получил награду</span>
        </li>
      </ul>

      <button class="round-result__ok" type="button" @click="game.dismissRoundResult()">ОК</button>
    </div>
  </div>
</template>

<style scoped>
.round-result {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

.round-result__panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: min(420px, calc(100vw - 2rem));
  padding: 1.5rem;
  border-radius: 16px;
  background: #fff;
  color: #1a2530;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
}

.round-result__title {
  margin: 0;
  font-size: 1.4rem;
  text-align: center;
  color: #4a2c16;
}

.round-result__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.round-result__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.65rem;
  border-radius: 8px;
  background: #f7f1e8;
  font-weight: 600;
}

.round-result__item--reward {
  background: #fdf3d8;
}

.dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.25);
  flex: none;
}

.round-result__ok {
  align-self: center;
  padding: 0.6rem 2rem;
  border: none;
  border-radius: 10px;
  background: #c0392b;
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
}

.round-result__ok:hover { filter: brightness(1.08); }
</style>
