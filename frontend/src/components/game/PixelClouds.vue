<script setup lang="ts">
// Облака: блок дублируется по горизонтали и медленно прокручивается (как фон, но в 4 раза медленнее).
const BASE = [
  { src: '/images/cloud_1.png', left: 0.03, top: 5, width: 190, dur: 9, delay: 0 },
  { src: '/images/cloud_2.png', left: 0.19, top: 17, width: 210, dur: 11, delay: 1.4 },
  { src: '/images/cloud_3.png', left: 0.35, top: 26, width: 180, dur: 8, delay: 0.7 },
  { src: '/images/cloud_4.png', left: 0.51, top: 8, width: 230, dur: 12, delay: 2.1 },
  { src: '/images/cloud_5.png', left: 0.67, top: 22, width: 170, dur: 9.5, delay: 0.3 },
  { src: '/images/cloud_6.png', left: 0.83, top: 13, width: 190, dur: 10.5, delay: 1.8 },
]

// Две копии на блок шириной 200% (для бесшовной прокрутки).
const clouds = BASE.flatMap((c) => [
  { ...c, left: c.left * 50 },
  { ...c, left: c.left * 50 + 50 },
])
</script>

<template>
  <div class="clouds">
    <img
      v-for="(c, i) in clouds"
      :key="i"
      class="cloud"
      :src="c.src"
      alt=""
      :style="{
        left: `${c.left}%`,
        top: `${c.top}%`,
        width: `${c.width}px`,
        animationDuration: `${c.dur}s`,
        animationDelay: `${c.delay}s`,
      }"
    />
  </div>
</template>

<style scoped>
.clouds {
  position: absolute;
  left: 0;
  top: 0;
  width: 200%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
  animation: clouds-scroll 48s linear infinite;
}

.cloud {
  position: absolute;
  height: auto;
  animation: cloud-drift 9s ease-in-out infinite;
}

@keyframes cloud-drift {
  0%,
  100% {
    transform: translate(0, 0);
  }
  25% {
    transform: translate(-3px, 1px);
  }
  50% {
    transform: translate(2px, -2px);
  }
  75% {
    transform: translate(-2px, 1px);
  }
}

@keyframes clouds-scroll {
  to {
    transform: translateX(-50%);
  }
}
</style>
