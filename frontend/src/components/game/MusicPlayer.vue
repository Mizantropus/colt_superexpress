<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const audio = ref<HTMLAudioElement | null>(null)
const toggle = ref<HTMLButtonElement | null>(null)
const volume = ref<HTMLInputElement | null>(null)

const playlist = ['/1.mp3', '/2.mp3']
let trackIndex = 0
let muted = false
let lastVolume = 0.2

function startPlayback() {
  audio.value?.play().catch((error: unknown) => {
    if ((error as Error)?.name === 'NotAllowedError') {
      window.addEventListener('pointerdown', startAfterInteraction, { once: true })
      window.addEventListener('keydown', startAfterInteraction, { once: true })
      return
    }
    console.error('Не удалось воспроизвести музыку:', error)
  })
}

function startAfterInteraction() {
  window.removeEventListener('pointerdown', startAfterInteraction)
  window.removeEventListener('keydown', startAfterInteraction)
  startPlayback()
}

function updateControls() {
  if (!audio.value || !toggle.value || !volume.value) return
  audio.value.muted = muted
  toggle.value.dataset.muted = String(muted)
  toggle.value.setAttribute('aria-pressed', String(muted))
  toggle.value.setAttribute('aria-label', muted ? 'Включить звук' : 'Отключить звук')
  volume.value.value = String(Math.round(audio.value.volume * 100))
}

function onToggle() {
  if (!audio.value) return
  if (muted) {
    muted = false
    audio.value.volume = lastVolume
  } else {
    if (audio.value.volume > 0) lastVolume = audio.value.volume
    muted = true
    audio.value.volume = 0
  }
  updateControls()
  if (!muted && audio.value.paused) startPlayback()
}

function onVolume() {
  if (!audio.value || !volume.value) return
  const value = Number(volume.value.value) / 100
  audio.value.volume = value
  muted = value === 0
  if (value > 0) lastVolume = value
  updateControls()
  if (!muted && audio.value.paused) startPlayback()
}

function onEnded() {
  if (!audio.value) return
  trackIndex = (trackIndex + 1) % playlist.length
  audio.value.src = playlist[trackIndex]
  startPlayback()
}

onMounted(() => {
  if (!audio.value) return
  audio.value.volume = 0.2
  audio.value.src = playlist[trackIndex]
  updateControls()
  startPlayback()
})

onBeforeUnmount(() => {
  window.removeEventListener('pointerdown', startAfterInteraction)
  window.removeEventListener('keydown', startAfterInteraction)
})
</script>

<template>
  <div class="music_player">
    <audio ref="audio" preload="auto" hidden @ended="onEnded" />
    <button
      id="music_toggle"
      ref="toggle"
      type="button"
      aria-label="Отключить звук"
      aria-pressed="false"
      data-muted="false"
      @click="onToggle"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 9v6h4l5 4V5L7 9H3z" />
        <path class="sound_waves" d="M16 9a5 5 0 0 1 0 6M19 5a10 10 0 0 1 0 14" />
        <path class="mute_mark" d="m16 9 5 6m0-6-5 6" />
      </svg>
    </button>
    <div class="volume_panel">
      <input
        ref="volume"
        type="range"
        min="0"
        max="100"
        value="20"
        aria-label="Громкость музыки"
        @input="onVolume"
      />
    </div>
  </div>
</template>