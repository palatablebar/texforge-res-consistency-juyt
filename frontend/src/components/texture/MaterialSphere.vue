<script setup lang="ts">
/**
 * Three.js 材质球：只消费后端产出的贴图 URL，前端不做像素生成。
 * WebGL 不可用时降级展示后端算好的 preview PNG。
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import { fileUrl } from '../../api/http'
import type { TextureVariant } from '../../types/texture'

const props = defineProps<{
  variant: TextureVariant | null
  envIntensity?: number
  rotation?: number
  exposure?: number
  tiling?: number
  normalScale?: number
}>()

const host = ref<HTMLDivElement | null>(null)
const fallback = ref(false)
const loading = ref(false)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let material: THREE.MeshPhysicalMaterial | null = null
let mesh: THREE.Mesh | null = null
let raf = 0
let textureCache: Record<string, THREE.Texture> = {}

function loadTexture(relPath: string | null | undefined, kind: 'artifacts' = 'artifacts'): THREE.Texture | null {
  if (!relPath) return null
  const url = fileUrl(kind, relPath)
  if (!textureCache[url]) {
    const loader = new THREE.TextureLoader()
    const texture = loader.load(url)
    texture.wrapS = THREE.RepeatWrapping
    texture.wrapT = THREE.RepeatWrapping
    texture.colorSpace = relPath.includes('base_color') ? THREE.SRGBColorSpace : THREE.NoColorSpace
    textureCache[url] = texture
  }
  return textureCache[url]
}

function applySettings() {
  if (!renderer || !material) return
  renderer.toneMappingExposure = props.exposure ?? 1
  material.envMapIntensity = props.envIntensity ?? 1
  material.normalScale = new THREE.Vector2(props.normalScale ?? 1, props.normalScale ?? 1)
  const tiling = Math.max(1, Math.round(props.tiling ?? 1))
  Object.values(textureCache).forEach((texture) => {
    texture.repeat.set(tiling, tiling)
    texture.needsUpdate = true
  })
  if (mesh) mesh.rotation.y = THREE.MathUtils.degToRad(props.rotation ?? 0)
}

function rebuildMaterial() {
  if (!scene || !mesh) return
  const paths = props.variant?.file_paths_json || {}
  const map = loadTexture(paths.base_color)
  const normalMap = loadTexture(paths.normal)
  const roughnessMap = loadTexture(paths.roughness)
  const metalnessMap = loadTexture(paths.metallic)
  const aoMap = loadTexture(paths.ao)
  if (!map) {
    fallback.value = true
    return
  }
  material = new THREE.MeshPhysicalMaterial({
    map,
    normalMap: normalMap || undefined,
    roughnessMap: roughnessMap || undefined,
    metalnessMap: metalnessMap || undefined,
    aoMap: aoMap || undefined,
    roughness: 1,
    metalness: 1,
    aoMapIntensity: 0.85,
    envMapIntensity: props.envIntensity ?? 1,
    clearcoat: 0,
  })
  mesh.material = material
  applySettings()
}

function init() {
  if (!host.value) return
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true })
  } catch {
    fallback.value = true
    return
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(host.value.clientWidth, host.value.clientHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = props.exposure ?? 1
  host.value.appendChild(renderer.domElement)

  scene = new THREE.Scene()
  const pmrem = new THREE.PMREMGenerator(renderer)
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture

  camera = new THREE.PerspectiveCamera(32, host.value.clientWidth / host.value.clientHeight, 0.1, 100)
  camera.position.set(0, 0.35, 4.1)

  const key = new THREE.DirectionalLight(0xffffff, 1.1)
  key.position.set(-2.2, 2.4, 2.6)
  scene.add(key)
  const rim = new THREE.DirectionalLight(0xffffff, 0.4)
  rim.position.set(2.4, -1.0, -1.6)
  scene.add(rim)

  const geometry = new THREE.SphereGeometry(1.35, 128, 128)
  material = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.8, metalness: 0.1 })
  mesh = new THREE.Mesh(geometry, material)
  scene.add(mesh)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.enablePan = false
  controls.minDistance = 2.4
  controls.maxDistance = 7

  rebuildMaterial()

  const animate = () => {
    raf = requestAnimationFrame(animate)
    controls?.update()
    if (mesh && !controls?.dragging) {
      // 保留用户拖动结果，rotation 由外部滑块控制初始角
    }
    if (renderer && scene && camera) renderer.render(scene, camera)
  }
  animate()

  window.addEventListener('resize', resize)
}

function resize() {
  if (!renderer || !camera || !host.value) return
  const width = host.value.clientWidth
  const height = host.value.clientHeight
  if (!width || !height) return
  renderer.setSize(width, height)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

onMounted(() => {
  init()
  window.setTimeout(() => {
    if (!props.variant) return
    loading.value = true
    try {
      rebuildMaterial()
    } finally {
      loading.value = false
    }
  }, 120)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
  controls?.dispose()
  renderer?.dispose()
  if (host.value) host.value.innerHTML = ''
})

watch(() => props.variant?.id, () => rebuildMaterial())
watch(() => [props.envIntensity, props.exposure, props.tiling, props.normalScale], () => applySettings())
watch(() => props.rotation, (value) => {
  if (mesh) mesh.rotation.y = THREE.MathUtils.degToRad(value ?? 0)
})
</script>

<template>
  <div class="sphere-wrap">
    <div ref="host" class="sphere-host" />
    <img
      v-if="fallback && variant?.preview_path"
      class="sphere-fallback"
      :src="fileUrl('previews', variant.preview_path)"
      alt="材质球预览"
    />
    <div v-if="!variant" class="sphere-empty mono-label">选择一条配方与变体</div>
    <div class="sphere-meta mono-label">
      MeshPhysicalMaterial · PMREM · OrbitControls
      <span v-if="loading"> · 贴图加载中</span>
    </div>
  </div>
</template>

<style scoped>
.sphere-wrap {
  position: relative;
  width: 100%;
  height: min(46vh, 430px);
  min-height: 260px;
  background: radial-gradient(circle at 50% 42%, var(--paper) 0%, var(--paper-2) 74%);
  border: 1px solid var(--paper-edge);
  overflow: hidden;
}
.sphere-host {
  position: absolute;
  inset: 0;
}
.sphere-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.sphere-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sphere-meta {
  position: absolute;
  left: 10px;
  bottom: 8px;
  font-size: 9px;
  letter-spacing: 0.08em;
}
</style>
