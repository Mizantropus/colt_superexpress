// Синтез звуковых эффектов через Web Audio API (без внешних файлов).

let audioCtx: AudioContext | null = null
let enabled = true

function ctx(): AudioContext | null {
  try {
    if (!audioCtx) {
      audioCtx = new AudioContext()
    }
    if (audioCtx.state === 'suspended') {
      void audioCtx.resume()
    }
    return audioCtx
  } catch {
    return null
  }
}

export function setSoundEnabled(value: boolean) {
  enabled = value
}

function noiseBurst(duration: number, decay: number, volume: number) {
  if (!enabled) return
  const c = ctx()
  if (!c) return
  const now = c.currentTime
  const size = Math.max(1, Math.floor(c.sampleRate * duration))
  const buffer = c.createBuffer(1, size, c.sampleRate)
  const data = buffer.getChannelData(0)
  for (let i = 0; i < size; i++) {
    const t = i / size
    data[i] = (Math.random() * 2 - 1) * Math.exp(-t * decay)
  }
  const src = c.createBufferSource()
  src.buffer = buffer
  const gain = c.createGain()
  gain.gain.value = volume
  src.connect(gain)
  gain.connect(c.destination)
  src.start(now)
}

function tone(freq: number, duration: number, volume: number, type: OscillatorType = 'square') {
  if (!enabled) return
  const c = ctx()
  if (!c) return
  const now = c.currentTime
  const osc = c.createOscillator()
  osc.type = type
  osc.frequency.value = freq
  const gain = c.createGain()
  gain.gain.setValueAtTime(volume, now)
  gain.gain.exponentialRampToValueAtTime(0.001, now + duration)
  osc.connect(gain)
  gain.connect(c.destination)
  osc.start(now)
  osc.stop(now + duration)
}

export function playShot() {
  noiseBurst(0.12, 25, 0.5)
}

export function playMove() {
  noiseBurst(0.06, 30, 0.18)
}

export function playCard() {
  tone(650, 0.08, 0.12, 'triangle')
}

export function playHorse() {
  for (let i = 0; i < 4; i++) {
    window.setTimeout(() => tone(110 + i * 15, 0.07, 0.15, 'square'), i * 140)
  }
}

export function playDetach() {
  noiseBurst(0.35, 7, 0.4)
}

export function playTurn() {
  tone(280, 0.09, 0.12, 'triangle')
}