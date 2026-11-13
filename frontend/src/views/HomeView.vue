<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useConnectionStore } from '@/stores/connection'
import { useRoomStore } from '@/stores/room'

const router = useRouter()
const connection = useConnectionStore()
const room = useRoomStore()

const name = ref('')
const joinCode = ref('')
const maxPlayers = ref(3)

watch(
  () => room.status,
  (s) => {
    if (s === 'playing' || s === 'finished') router.push('/game')
  },
)

function onCreate() {
  room.createRoom(name.value || 'Игрок', Number(maxPlayers.value))
}

function onJoin() {
  room.joinRoom(joinCode.value.trim().toUpperCase(), name.value || 'Игрок')
}
</script>

<template>
  <section class="lobby">
    <header class="lobby__header">
      <h1 class="lobby__title">Кольт Суперэкспресс</h1>
      <p class="lobby__status">
        <span class="dot" :class="`dot--${connection.status}`"></span>
        {{ connection.status }}
      </p>
    </header>

    <div v-if="!room.roomCode" class="lobby__forms">
      <!-- 1. Имя -->
      <section class="panel panel--block">
        <div class="panel__head">
          <span class="panel__num">1</span>
          <h2 class="panel__title">Имя</h2>
        </div>
        <input
          v-model="name"
          type="text"
          maxlength="24"
          placeholder="Введите имя"
          class="input"
        />
      </section>

      <!-- 2. Создание комнаты -->
      <section class="panel panel--block">
        <div class="panel__head">
          <span class="panel__num">2</span>
          <h2 class="panel__title">Создать комнату</h2>
        </div>
        <p class="panel__hint">Количество игроков</p>
        <div class="panel__chips">
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            class="chip"
            :class="{ 'chip--active': maxPlayers === n + 2 }"
            @click="maxPlayers = n + 2"
          >
            {{ n + 2 }}
          </button>
        </div>
        <button class="btn" type="button" @click="onCreate">Создать</button>
      </section>

      <!-- 3. Вход по коду -->
      <section class="panel panel--block">
        <div class="panel__head">
          <span class="panel__num">3</span>
          <h2 class="panel__title">Вход по коду</h2>
        </div>
        <input
          v-model="joinCode"
          type="text"
          maxlength="6"
          placeholder="ABC123"
          class="input input--code"
        />
        <button class="btn" type="button" @click="onJoin">Войти</button>
      </section>

      <p v-if="room.error" class="lobby__error">{{ room.error }}</p>
    </div>

    <div v-else class="panel lobby__room">
      <p class="lobby__code">
        Код комнаты: <strong>{{ room.roomCode }}</strong>
      </p>

      <div class="lobby__roomhead">
        <p class="lobby__count">Игроков: {{ room.players.length }} / {{ room.maxPlayers }}</p>
        <button
          v-if="room.isHost"
          class="btn btn--ghost btn--small"
          :disabled="room.players.length >= room.maxPlayers"
          @click="room.addBot()"
        >
          + Бот
        </button>
      </div>

      <ul class="lobby__players">
        <li v-for="p in room.players" :key="p.id">
          {{ p.name }}<template v-if="p.isHost"> — хост</template><template v-else-if="p.isBot"> — бот</template>
        </li>
      </ul>

      <div class="lobby__actions">
        <button
          v-if="room.isHost"
          class="btn"
          :disabled="!room.canStart"
          @click="room.startGame()"
        >
          Начать игру
        </button>
        <button class="btn btn--ghost" @click="room.leaveRoom()">Покинуть</button>
      </div>

      <p v-if="room.error" class="lobby__error">{{ room.error }}</p>
    </div>
  </section>
</template>

<style scoped>
.lobby {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  min-height: 100%;
  padding: 2.5rem 1rem 2rem;
  color: #2a1a10;
  overflow-y: auto;
  background:
    radial-gradient(circle at 15% 0%, rgba(255, 255, 255, 0.5), transparent 45%),
    linear-gradient(165deg, #f9edd8 0%, #ecd6b6 55%, #dcc09a 100%);
}

.lobby__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  text-align: center;
}

.lobby__title {
  margin: 0;
  font-size: clamp(2rem, 5vw, 3rem);
  letter-spacing: 0.02em;
  color: #4a2c16;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
}

.lobby__status {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.85rem;
  color: #7a5a3c;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #bbb;
}

.dot--connected { background: #27ae60; }
.dot--connecting { background: #e6b23a; }
.dot--disconnected { background: #c0392b; }

.lobby__forms {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  width: 100%;
  max-width: 360px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 1.2rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 8px 24px rgba(74, 44, 22, 0.14);
}

.panel--block {
  width: 100%;
}

.panel__head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.2rem;
}

.panel__num {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #c0392b;
  color: #fff;
  font-weight: 700;
  font-size: 0.95rem;
  flex: none;
}

.panel__title {
  margin: 0;
  font-size: 1.05rem;
  color: #4a2c16;
}

.panel__hint {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: #7a5a3c;
}

.panel__chips {
  display: flex;
  gap: 0.5rem;
}

.chip {
  flex: 1;
  padding: 0.55rem 0;
  border: 1px solid #c9b394;
  border-radius: 10px;
  background: #fff;
  color: #4a2c16;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.chip--active {
  background: #c0392b;
  border-color: #c0392b;
  color: #fff;
}

.input {
  padding: 0.65rem 0.75rem;
  border: 1px solid #c9b394;
  border-radius: 10px;
  font-size: 1rem;
  background: #fff;
  color: #2a1a10;
}

.input:focus {
  outline: none;
  border-color: #c0392b;
  box-shadow: 0 0 0 3px rgba(192, 57, 43, 0.15);
}

.input--code {
  text-transform: uppercase;
  letter-spacing: 0.15em;
  text-align: center;
  font-weight: 700;
}

.btn {
  padding: 0.7rem 1rem;
  border: none;
  border-radius: 10px;
  background: #c0392b;
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: filter 0.15s;
}

.btn:hover { filter: brightness(1.08); }

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--ghost {
  background: transparent;
  border: 1px solid #4a2c16;
  color: #4a2c16;
}

.btn--small {
  padding: 0.35rem 0.7rem;
  font-size: 0.85rem;
}

.lobby__error {
  margin: 0;
  color: #c0392b;
  font-weight: 700;
  text-align: center;
}

.lobby__room {
  width: 100%;
  max-width: 360px;
}

.lobby__code {
  margin: 0;
  font-size: 1.3rem;
  color: #4a2c16;
}

.lobby__count {
  margin: 0;
  color: #7a5a3c;
}

.lobby__roomhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}

.lobby__players {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
}

.lobby__players li {
  padding: 0.4rem 0;
  border-bottom: 1px solid #e8ddcc;
}

.lobby__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}
</style>
