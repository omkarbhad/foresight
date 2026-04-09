<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="foresight-logo">
    <!-- Eye shape -->
    <path d="M2 12C2 12 5.5 5 12 5s10 7 10 7-3.5 7-10 7S2 12 2 12z" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <!-- Iris -->
    <circle cx="12" cy="12" r="3.5" stroke="rgba(255,255,255,0.35)" stroke-width="1.5"/>
    <!-- Pupil -->
    <circle cx="12" cy="12" r="1.5" fill="#6366f1"/>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: Number, default: 18 },
})
</script>

<style scoped>
.foresight-logo {
  display: block;
  flex-shrink: 0;
}
</style>
