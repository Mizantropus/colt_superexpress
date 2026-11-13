import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import type { ServerMessage } from '@/api/ws'
import { useConnectionStore } from './connection'
import { clearSession, saveSession } from '@/game/session'
import { useGameStore } from './game'

export interface LobbyPlayer {
  id: string
  name: string
  isHost: boolean
  isBot: boolean
}

export type RoomStatus = 'waiting' | 'playing' | 'finished'

export const useRoomStore = defineStore('room', () => {
  const connection = useConnectionStore()
  const gameStore = useGameStore()

  const roomCode = ref<string | null>(null)
  const players = ref<LobbyPlayer[]>([])
  const hostId = ref<string | null>(null)
  const maxPlayers = ref(3)
  const status = ref<RoomStatus | null>(null)
  const myPlayerId = ref<string | null>(null)
  const myToken = ref<string | null>(null)
  const error = ref<string | null>(null)

  const isHost = computed(() => myPlayerId.value !== null && myPlayerId.value === hostId.value)
  const canStart = computed(
    () => isHost.value && players.value.length >= 3 && status.value === 'waiting',
  )

  function applyPlayers(list: LobbyPlayer[]) {
    players.value = (list ?? []).map((p) => ({
      id: p.id,
      name: p.name,
      isHost: Boolean(p.isHost),
      isBot: Boolean(p.isBot),
    }))
  }

  function reset() {
    roomCode.value = null
    players.value = []
    hostId.value = null
    maxPlayers.value = 3
    status.value = null
    myPlayerId.value = null
    myToken.value = null
    error.value = null
    clearSession()
  }

  function setupListeners() {
    connection.on('created', (m: ServerMessage) => {
      roomCode.value = String(m.room_code ?? '')
      myPlayerId.value = String(m.player_id ?? '')
      myToken.value = String(m.token ?? '')
      hostId.value = String(m.host_id ?? '')
      maxPlayers.value = Number(m.max_players ?? 3)
      status.value = (m.status as RoomStatus) ?? 'waiting'
      applyPlayers(m.players as LobbyPlayer[])
      error.value = null
      if (myToken.value && roomCode.value && myPlayerId.value) {
        saveSession({ token: myToken.value, roomCode: roomCode.value, playerId: myPlayerId.value })
      }
    })

    connection.on('joined', (m: ServerMessage) => {
      roomCode.value = String(m.room_code ?? '')
      myPlayerId.value = String(m.player_id ?? '')
      myToken.value = String(m.token ?? '')
      hostId.value = String(m.host_id ?? '')
      maxPlayers.value = Number(m.max_players ?? 3)
      status.value = (m.status as RoomStatus) ?? 'waiting'
      applyPlayers(m.players as LobbyPlayer[])
      error.value = null
      if (myToken.value && roomCode.value && myPlayerId.value) {
        saveSession({ token: myToken.value, roomCode: roomCode.value, playerId: myPlayerId.value })
      }
    })

    connection.on('resync', (m: ServerMessage) => {
      roomCode.value = String(m.room_code ?? '')
      myPlayerId.value = String(m.player_id ?? '')
      hostId.value = String(m.host_id ?? '')
      maxPlayers.value = Number(m.max_players ?? 3)
      status.value = (m.status as RoomStatus) ?? 'waiting'
      applyPlayers(m.players as LobbyPlayer[])
      error.value = null
      if (m.state) {
        gameStore.setPlanningTimeout(Number(m.planning_timeout ?? 60))
        gameStore.setPlanningDeadline(Number(m.planning_deadline ?? 0))
        gameStore.setState((m.state ?? {}) as Record<string, unknown>)
      }
    })

    connection.on('player_joined', (m: ServerMessage) => {
      players.value.push({
        id: String(m.player_id),
        name: String(m.player_name ?? 'Игрок'),
        isHost: false,
        isBot: Boolean(m.is_bot),
      })
    })

    connection.on('player_left', (m: ServerMessage) => {
      players.value = players.value.filter((p) => p.id !== String(m.player_id))
    })

    connection.on('left', () => reset())

    connection.on('game_finished', () => clearSession())

    connection.on('game_started', (m: ServerMessage) => {
      status.value = 'playing'
      applyPlayers(m.players as LobbyPlayer[])
      gameStore.setPlanningTimeout(Number(m.planning_timeout ?? 60))
      gameStore.setState((m.state ?? {}) as Record<string, unknown>)
    })

    connection.on('error', (m: ServerMessage) => {
      error.value = String(m.message ?? 'Ошибка')
    })
  }

  function createRoom(name: string, max: number) {
    error.value = null
    connection.send('create', { player_name: name, max_players: max })
  }

  function joinRoom(code: string, name: string) {
    error.value = null
    connection.send('join', { room_code: code, player_name: name })
  }

  function leaveRoom() {
    connection.send('leave')
  }

  function startGame() {
    connection.send('start_game')
  }

  function addBot() {
    connection.send('add_bot')
  }

  return {
    roomCode, players, hostId, maxPlayers, status, myPlayerId, myToken, error,
    isHost, canStart,
    setupListeners, reset, createRoom, joinRoom, leaveRoom, startGame, addBot,
  }
})