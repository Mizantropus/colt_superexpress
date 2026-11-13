// Простой WebSocket-клиент: подключение, отправка, подписка на события,
// базовый авто-реконнект.

export type ServerMessage = {
  type: string
  [key: string]: unknown
}

type MessageHandler = (message: ServerMessage) => void

export const DEFAULT_URL =
  (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://localhost:8000/ws'

export class WsClient {
  private ws: WebSocket | null = null
  private readonly url: string
  private readonly handlers = new Map<string, Set<MessageHandler>>()
  private readonly pending: string[] = []
  private reconnectTimer: number | null = null
  private reconnectDelay = 1000
  private manuallyClosed = false

  constructor(url: string = DEFAULT_URL) {
    this.url = url
  }

  connect(): void {
    this.manuallyClosed = false
    this.ws = new WebSocket(this.url)

    this.ws.addEventListener('open', () => {
      this.reconnectDelay = 1000
      this._dispatch({ type: '__open__' })
      this._flush()
    })

    this.ws.addEventListener('message', (event) => {
      try {
        const message = JSON.parse(String(event.data)) as ServerMessage
        this._dispatch(message)
      } catch {
        // игнорируем невалидные сообщения
      }
    })

    this.ws.addEventListener('close', () => {
      this._dispatch({ type: '__close__' })
      if (!this.manuallyClosed) {
        this._scheduleReconnect()
      }
    })

    this.ws.addEventListener('error', () => {
      // 'close' сработает следом и запустит реконнект
    })
  }

  send(type: string, payload: Record<string, unknown> = {}): void {
    const data = JSON.stringify({ type, ...payload })
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data)
    } else {
      this.pending.push(data)
    }
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(handler)
    return () => this.handlers.get(type)?.delete(handler)
  }

  disconnect(): void {
    this.manuallyClosed = true
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  private _flush(): void {
    while (this.pending.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(this.pending.shift()!)
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer !== null) return
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, this.reconnectDelay)
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 10_000)
  }

  private _dispatch(message: ServerMessage): void {
    this.handlers.get(message.type)?.forEach((handler) => handler(message))
    this.handlers.get('*')?.forEach((handler) => handler(message))
  }
}