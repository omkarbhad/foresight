<template>
  <canvas ref="cvs" class="floating-canvas" aria-hidden="true"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const cvs = ref(null)
let ctx, w, h, raf, objects = []

// Pixel art shapes (1 = fill, 0 = empty)
const SHAPES = [
  // Ghost
  { layout: [[0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,0,1,0,1,1],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[1,0,1,1,1,0,1]], colors: ['#00ffcc','#ff00aa','#8800ff','#ffaa00','#0088ff'] },
  // Invader crab
  { layout: [[0,0,1,0,0,0,1,0,0],[0,0,0,1,0,1,0,0,0],[0,0,1,1,1,1,1,0,0],[0,1,0,1,1,1,0,1,0],[1,1,1,1,1,1,1,1,1],[1,0,1,1,1,1,1,0,1],[1,0,1,0,0,0,1,0,1]], colors: ['#ff3333','#ffee00','#00ff44','#0088ff'] },
  // Invader squid
  { layout: [[0,0,0,1,1,0,0,0],[0,0,1,1,1,1,0,0],[0,1,1,1,1,1,1,0],[1,1,0,1,1,0,1,1],[1,1,1,1,1,1,1,1],[0,1,0,0,0,0,1,0]], colors: ['#ff00aa','#8800ff','#00ffcc','#ffaa00'] },
  // Pac-man
  { layout: [[0,1,1,1,1,0],[1,1,1,1,1,1],[1,1,1,0,0,0],[1,1,1,1,1,1],[0,1,1,1,1,0]], colors: ['#ffee00'] },
  // Heart
  { layout: [[0,1,0,1,0],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]], colors: ['#ff3333','#ff00aa'] },
  // Diamond
  { layout: [[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]], colors: ['#00ffcc','#0088ff','#8800ff'] },
  // Star
  { layout: [[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,1,1,1,0],[0,1,0,1,0]], colors: ['#ffaa00','#ffee00'] },
  // Arrow
  { layout: [[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0]], colors: ['#0088ff','#00ffcc'] },
]

function createObject() {
  const shape = SHAPES[Math.floor(Math.random() * SHAPES.length)]
  const color = shape.colors[Math.floor(Math.random() * shape.colors.length)]
  const scale = 2 + Math.random() * 3
  const depth = 0.15 + Math.random() * 0.85 // 0=far, 1=near
  return {
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.3 * depth,
    vy: -0.2 - Math.random() * 0.4 * depth,
    rotation: Math.random() * Math.PI * 2,
    rotSpeed: (Math.random() - 0.5) * 0.005,
    scale,
    depth,
    opacity: 0.03 + depth * 0.06,
    color,
    layout: shape.layout,
  }
}

function drawPixelShape(obj) {
  const { x, y, scale, layout, color, opacity, rotation } = obj
  const rows = layout.length
  const cols = layout[0].length
  const pxSize = scale

  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(rotation)
  ctx.globalAlpha = opacity
  ctx.fillStyle = color

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (layout[r][c]) {
        ctx.fillRect(
          (c - cols / 2) * pxSize,
          (r - rows / 2) * pxSize,
          pxSize - 0.5,
          pxSize - 0.5
        )
      }
    }
  }
  ctx.restore()
}

function animate() {
  ctx.clearRect(0, 0, w, h)

  for (const obj of objects) {
    obj.x += obj.vx
    obj.y += obj.vy
    obj.rotation += obj.rotSpeed

    // Wrap around
    if (obj.y < -40) { obj.y = h + 40; obj.x = Math.random() * w }
    if (obj.x < -40) obj.x = w + 40
    if (obj.x > w + 40) obj.x = -40

    drawPixelShape(obj)
  }

  raf = requestAnimationFrame(animate)
}

function resize() {
  const canvas = cvs.value
  if (!canvas) return
  w = canvas.width = window.innerWidth
  h = canvas.height = window.innerHeight
}

onMounted(() => {
  const canvas = cvs.value
  if (!canvas) return
  ctx = canvas.getContext('2d')
  resize()

  // Create objects
  const count = Math.min(40, Math.floor((w * h) / 25000))
  for (let i = 0; i < count; i++) {
    objects.push(createObject())
  }

  window.addEventListener('resize', resize)
  raf = requestAnimationFrame(animate)
})

onUnmounted(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
})
</script>

<style scoped>
.floating-canvas {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
</style>
