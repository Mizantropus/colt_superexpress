<script setup lang="ts">
import { onMounted } from 'vue'

import { useConnectionStore } from '@/stores/connection'
import { useGameStore } from '@/stores/game'
import { useRoomStore } from '@/stores/room'

onMounted(() => {
  const connection = useConnectionStore()
  const room = useRoomStore()
  const game = useGameStore()

  connection.connect()
  room.setupListeners()
  game.setupListeners()
})
</script>

<template>
  <div class="app-shell">
    <RouterView />
  </div>
</template>

<style scoped>
.app-shell {
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}
</style>