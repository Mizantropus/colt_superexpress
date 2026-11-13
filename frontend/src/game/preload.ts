// Фоновая предзагрузка спрайтов и карт, чтобы во время игры не было подгрузок.
import { ALL_PLAYER_COLORS, ACTION_CARD_PREFIX } from './constants'

const SPRITE_NAMES = [
  'walking_east',
  'staying_east',
  'shoot',
  'shoot-from-hip',
  'shoot-itself',
  'rotate',
  'laying',
  'horse',
  'climbing',
  'fallforvard',
  'fallback',
  'gettingup',
  'slazdown',
]

const EXTRA_IMAGES = [
  '/images/delorian.png',
  '/images/delorian_wheel.png',
  '/images/lokomotive_wheel.png',
  '/images/vagon_wheel.png',
  '/images/lokomotiv.png',
  '/images/vagon.png',
  '/images/lokomotive_small_wheel.png',
  '/images/skull.png',
  '/images/sky.jpg',
  '/images/mountains.png',
  '/images/reels.jpg',
  '/images/ornament.jpg',
  '/images/background.jpg',
  '/images/cloud_1.png',
  '/images/cloud_2.png',
  '/images/cloud_3.png',
  '/images/cloud_4.png',
  '/images/cloud_5.png',
  '/images/cloud_6.png',
]

let started = false

export function preloadGameAssets(): void {
  if (started) return
  started = true

  for (const color of ALL_PLAYER_COLORS) {
    for (const name of SPRITE_NAMES) {
      preload(`/images/${name}_${color}.png`)
    }
    for (const prefix of Object.values(ACTION_CARD_PREFIX)) {
      preload(`/images/${prefix}_${color}.jpg`)
    }
  }

  for (const url of EXTRA_IMAGES) {
    preload(url)
  }
}

function preload(url: string): void {
  const img = new Image()
  img.src = url
}
