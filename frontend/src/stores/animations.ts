import { ref } from 'vue'
import { defineStore } from 'pinia'

export type AnimationStep = () => Promise<void>

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const useAnimationStore = defineStore('animations', () => {
  const queue = ref<AnimationStep[]>([])
  const running = ref(false)

  async function run() {
    if (running.value) return
    running.value = true
    try {
      while (queue.value.length > 0) {
        const step = queue.value.shift()!
        try {
          await step()
        } catch (error) {
          console.error('Ошибка шага анимации:', error)
        }
      }
    } finally {
      running.value = false
    }
  }

  function enqueue(step: AnimationStep) {
    queue.value.push(step)
    void run()
  }

  function clear() {
    queue.value = []
  }

  return { queue, running, enqueue, clear }
})