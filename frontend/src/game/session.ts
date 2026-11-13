// Хранение текущей игровой сессии (код стола + токен) в localStorage,
// чтобы при обновлении страницы переподключиться к тому же столу.

export interface StoredSession {
  token: string
  roomCode: string
  playerId: string
}

const KEY = 'colt_superexpress_session'

export function loadSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as Partial<StoredSession>
    if (
      data &&
      typeof data.token === 'string' &&
      typeof data.roomCode === 'string' &&
      typeof data.playerId === 'string'
    ) {
      return { token: data.token, roomCode: data.roomCode, playerId: data.playerId }
    }
    return null
  } catch {
    return null
  }
}

export function saveSession(session: StoredSession): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(session))
  } catch {
    /* ignore */
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* ignore */
  }
}
