<script setup lang="ts">
const model = defineModel<string>({ required: true })
const emit = defineEmits<{ uploaded: [url: string] }>()
const { apiFetch } = useApi()
const toast = useToast()

const mode = ref<'url' | 'upload'>('url')
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

async function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await apiFetch<{ url: string }>('/uploads/logo/', { method: 'POST', body: fd as unknown as Record<string, unknown> })
    model.value = res.url
    await nextTick()
    emit('uploaded', res.url)
    toast.add({ title: 'Logo subido y guardado', color: 'primary' })
  } catch (err: unknown) {
    const e = err as { response?: { data?: { error?: string } } }
    toast.add({ title: e.response?.data?.error ?? 'Error al subir el archivo', color: 'error' })
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function clearLogo() {
  model.value = ''
  emit('uploaded', '')
}
</script>

<template>
  <div class="space-y-2">
    <!-- Tabs -->
    <div class="flex gap-1 p-1 bg-slate-100 rounded-lg w-fit">
      <button
        type="button"
        class="px-3 py-1 rounded-md text-xs font-medium transition-all"
        :class="mode === 'url' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
        @click="mode = 'url'"
      >
        <UIcon name="i-lucide-link" class="inline w-3 h-3 mr-1" /> URL
      </button>
      <button
        type="button"
        class="px-3 py-1 rounded-md text-xs font-medium transition-all"
        :class="mode === 'upload' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
        @click="mode = 'upload'"
      >
        <UIcon name="i-lucide-upload" class="inline w-3 h-3 mr-1" /> Subir imagen
      </button>
    </div>

    <!-- Preview + input -->
    <div class="flex gap-3 items-center">
      <div class="w-12 h-12 rounded-xl border border-slate-200 bg-white flex items-center justify-center overflow-hidden flex-shrink-0">
        <img v-if="model" :src="model" alt="logo" class="w-full h-full object-contain" @error="($event.target as HTMLImageElement).style.display = 'none'">
        <UIcon v-else name="i-lucide-image" class="text-slate-300 w-6 h-6" />
      </div>

      <div v-if="mode === 'url'" class="flex-1 flex gap-2">
        <UInput v-model="model" class="flex-1 font-mono text-xs" placeholder="https://..." />
        <UButton v-if="model" size="sm" variant="ghost" color="error" icon="i-lucide-x" @click="clearLogo" />
      </div>

      <div v-else class="flex-1 flex gap-2 items-center">
        <input
          ref="fileInput"
          type="file"
          accept="image/png,image/jpeg,image/webp,image/svg+xml,image/gif"
          class="hidden"
          @change="onFileChange"
        >
        <UButton
          variant="outline"
          icon="i-lucide-upload"
          :loading="uploading"
          @click="fileInput?.click()"
        >
          {{ uploading ? 'Subiendo...' : 'Elegir archivo' }}
        </UButton>
        <UButton v-if="model" size="sm" variant="ghost" color="error" icon="i-lucide-x" @click="clearLogo">
          Quitar
        </UButton>
        <span class="text-xs text-slate-400">PNG, JPG, WEBP, SVG · máx 2 MB</span>
      </div>
    </div>
  </div>
</template>
