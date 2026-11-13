import { ref } from 'vue'
import { defineStore } from 'pinia'

/**
 * Заглушка стора сессии игрока.
 * Реальная логика (player_token, подключение к комнате) — в пунктах 23 и 35.
 */
export const useSessionStore = defineStore('session', () => {
  const playerId = ref<string | null>(null)
  const playerName = ref<string>('')

  return { playerId, playerName }
})