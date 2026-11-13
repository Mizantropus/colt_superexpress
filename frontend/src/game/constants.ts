export const CAR_WIDTH = 390
export const LOCOMOTIVE_INDEX = 1
export const STANDING_WIDTH = 48
export const LAYING_WIDTH = 63
// Полный набор цветов (по спрайтам в game.scss). Пока активны только красный
// и жёлтый — спрайты остальных ещё не загружены.
export const ALL_PLAYER_COLORS = ['red', 'yellow', 'black', 'green', 'blue', 'white', 'purple', 'brown']
export const PLAYER_COLORS = ALL_PLAYER_COLORS

export const COLOR_NAMES: Record<string, string> = {
  red: 'красный',
  yellow: 'жёлтый',
  black: 'чёрный',
  green: 'зелёный',
  blue: 'синий',
  white: 'белый',
  purple: 'фиолетовый',
  brown: 'коричневый',
}

export const COLOR_HEX: Record<string, string> = {
  red: '#c0392b',
  yellow: '#e0a91f',
  black: '#2b3a42',
  green: '#27ae60',
  blue: '#2980b9',
  white: '#ecf0f1',
  purple: '#8e44ad',
  brown: '#8b5a2b',
}

// Нижний отступ спрайта ковбоя от низа обёртки (уровень внутри/крыша).
export const INSIDE_BOTTOM = 35
export const ROOF_BOTTOM = 131

export interface ActionMeta {
  id: string
  label: string
  icon: string
}

export const ACTION_META: ActionMeta[] = [
  { id: 'move', label: 'Переместиться', icon: '🚶' },
  { id: 'change_level', label: 'Сменить уровень', icon: '🪜' },
  { id: 'turn_around', label: 'Развернуться', icon: '🔄' },
  { id: 'shoot', label: 'Выстрел', icon: '🔫' },
  { id: 'horse', label: 'Лошадь', icon: '🐴' },
  { id: 'hip_fire', label: 'Выстрел от бедра', icon: '🤠' },
]

export const ACTION_META_BY_ID: Record<string, ActionMeta> = Object.fromEntries(
  ACTION_META.map((a) => [a.id, a]),
)

// Префиксы файлов карт действий (картинки разложены по цветам).
export const ACTION_CARD_PREFIX: Record<string, string> = {
  move: 'move_card',
  change_level: 'change_level_card',
  turn_around: 'rotate_card',
  shoot: 'shoot_card',
  horse: 'horse_card',
  hip_fire: 'shoot_from_hip_card',
}

export function cardImage(actionId: string, color: string): string {
  const prefix = ACTION_CARD_PREFIX[actionId] ?? actionId
  return `/images/${prefix}_${color}.jpg`
}