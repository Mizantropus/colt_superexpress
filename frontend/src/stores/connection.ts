import { ref } from 'vue'
import { defineStore } from 'pinia'

import { WsClient, DEFAULT_URL, type ServerMessage } from '@/api/ws'
import { loadSession } from '@/game/session'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

export const useConnectionStore = defineStore('connection', () => {
  const status = ref<ConnectionStatus>('disconnected')
  const lastMessage = ref<ServerMessage | null>(null)
  const lastPongMs = ref<number | null>(null)

  let client: WsClient | null = null
  let pingStartedAt = 0

  function ensureClient(url?: string): WsClient {
    if (!client) {
      client = new WsClient(url)
      client.on('__open__', () => {
        status.value = 'connected'
      })
      client.on('__close__', () => {
        status.value = 'disconnected'
      })
      client.on('*', (message) => {
        lastMessage.value = message
      })
      client.on('pong', () => {
        if (pingStartedAt > 0) {
          lastPongMs.value = Math.round(performance.now() - pingStartedAt)
        }
      })
    }
    return client
  }

  function connect(url?: string): void {
    status.value = 'connecting'
    const base = url ?? DEFAULT_URL
    const session = loadSession()
    const full = session?.token
      ? `${base}${base.includes('?') ? '&' : '?'}token=${encodeURIComponent(session.token)}`
      : base
    ensureClient(full).connect()
  }

  function on(type: string, handler: (message: ServerMessage) => void): () => void {
    return ensureClient().on(type, handler)
  }

  function send(type: string, payload: Record<string, unknown> = {}): void {
    ensureClient().send(type, payload)
  }

  function ping(): void {
    pingStartedAt = performance.now()
    send('ping')
  }

  function disconnect(): void {
    client?.disconnect()
    client = null
    status.value = 'disconnected'
  }

  return { status, lastMessage, lastPongMs, connect, on, send, ping, disconnect }
})