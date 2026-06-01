<script setup lang="ts">
definePageMeta({ middleware: ['tenant', 'auth'] })

const support = useSupportStore()
const tenant = useTenantStore()
const toast = useToast()

const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const filter = ref<'all' | 'open' | 'assigned' | 'closed'>('all')

const filteredConversations = computed(() => {
  if (filter.value === 'all') return support.conversations
  return support.conversations.filter(c => c.status === filter.value)
})

const STATUS_LABEL = {
  open: 'Esperando',
  assigned: 'Activa',
  closed: 'Cerrada'
}

const STATUS_COLOR = {
  open: 'bg-amber-100 text-amber-700 ring-amber-200',
  assigned: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
  closed: 'bg-slate-100 text-slate-600 ring-slate-200'
}

async function refresh() {
  await support.fetchConversations()
}

async function selectConversation(id: string) {
  await support.openConversation(id)
  await scrollToBottom()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  support.sendMessage(text)
  await scrollToBottom()
}

// Respuestas predeterminadas que el agente puede insertar/enviar con un click
const QUICK_REPLIES = [
  '¡Hola! ¿En qué te puedo ayudar?',
  'Dame un momento mientras reviso tu información.',
  '¿Me podés confirmar tu nombre completo?',
  'Para agendar una cita podés hacerlo en la sección "Agendar".',
  'Te paso con un especialista, un momento por favor.',
  'Gracias por contactarnos. ¿Hay algo más en lo que pueda ayudarte?',
  'Vamos a confirmar la información y te aviso por correo.',
  'Una disculpa por la espera.'
]
const showQuickReplies = ref(false)

function insertQuickReply(text: string) {
  inputText.value = text
  showQuickReplies.value = false
}

async function sendQuickReply(text: string) {
  support.sendMessage(text)
  showQuickReplies.value = false
  await scrollToBottom()
}

const aiSuggesting = ref(false)
const { apiFetch } = useApi()

const attachInput = ref<HTMLInputElement | null>(null)
const uploadingAttachment = ref(false)

function pickAttachment() {
  attachInput.value?.click()
}

async function onAttachmentChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!support.activeId) return
  if (file.size > 10 * 1024 * 1024) {
    toast.add({ title: 'La imagen no puede pesar más de 10 MB', color: 'error' })
    return
  }
  uploadingAttachment.value = true
  try {
    const auth = useAuthStore()
    const config = useRuntimeConfig()
    const fd = new FormData()
    fd.append('image', file)
    fd.append('sender', 'agent')
    const url = `${config.public.apiBase}/support/conversations/${support.activeId}/upload-attachment/`
    const headers: Record<string, string> = {}
    if (auth.access) headers.Authorization = `Bearer ${auth.access}`
    const res = await fetch(url, { method: 'POST', body: fd, headers })
    if (!res.ok) throw new Error('upload failed')
    // El backend hace broadcast → el WS recibe el mensaje, no necesitamos hacer nada acá
  }
  catch {
    toast.add({ title: 'No se pudo subir la imagen', color: 'error' })
  }
  finally {
    uploadingAttachment.value = false
    if (input) input.value = ''
  }
}

async function suggestWithAI() {
  if (!support.activeId) return
  aiSuggesting.value = true
  try {
    const res = await apiFetch<{ reply: string, unavailable?: boolean, detail?: string }>(
      `/support/conversations/${support.activeId}/ai-suggest-reply/`,
      { method: 'POST' }
    )
    if (res.reply) {
      inputText.value = res.reply
    } else if (res.unavailable) {
      toast.add({ title: 'IA no disponible en la demo', description: res.detail, color: 'info' })
    } else {
      toast.add({ title: 'La IA no pudo generar una sugerencia', color: 'warning' })
    }
  }
  catch {
    toast.add({ title: 'Error al pedir sugerencia a la IA', color: 'error' })
  }
  finally {
    aiSuggesting.value = false
  }
}

const showCloseModal = ref(false)
const closing = ref(false)

function closeChat() {
  showCloseModal.value = true
}

async function confirmCloseChat() {
  closing.value = true
  try {
    support.closeActiveConversation()
    showCloseModal.value = false
  }
  finally {
    closing.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

watch(() => support.messages.length, scrollToBottom)

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })
}

function formatRelative(iso: string | null): string {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60000) return 'ahora'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} min`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} h`
  return new Date(iso).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
}

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  if (tenant.slug) support.connectWS(tenant.slug)
  await refresh()
  pollTimer = setInterval(refresh, 15000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  support.disconnect()
})
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">Soporte</h1>
        <p class="text-sm text-slate-400 mt-0.5">
          {{ filteredConversations.length }} conversaciones ·
          <span :class="support.wsStatus === 'connected' ? 'text-emerald-600' : 'text-slate-400'">
            {{ support.wsStatus === 'connected' ? 'En línea' : 'Desconectado' }}
          </span>
        </p>
      </div>
      <UButton variant="ghost" icon="i-lucide-refresh-cw" size="sm" @click="refresh">Actualizar</UButton>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 h-[calc(100vh-180px)] min-h-[500px]">

      <!-- Bandeja -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
        <div class="border-b border-slate-100 dark:border-slate-800 p-2 flex gap-1">
          <button
            v-for="f in (['all', 'open', 'assigned', 'closed'] as const)"
            :key="f"
            type="button"
            class="flex-1 text-xs font-medium px-2 py-1.5 rounded-lg transition-colors"
            :class="filter === f
              ? 'bg-violet-100 text-violet-700'
              : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800'"
            @click="filter = f"
          >
            {{ f === 'all' ? 'Todas' : STATUS_LABEL[f] }}
          </button>
        </div>

        <div class="flex-1 overflow-y-auto">
          <button
            v-for="c in filteredConversations"
            :key="c.id"
            type="button"
            class="w-full text-left px-4 py-3 border-b border-slate-100 dark:border-slate-800 transition-colors"
            :class="support.activeId === c.id
              ? 'bg-violet-50 dark:bg-violet-900/20'
              : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'"
            @click="selectConversation(c.id)"
          >
            <div class="flex items-start justify-between gap-2 mb-1">
              <p class="font-medium text-sm text-slate-800 dark:text-slate-100 truncate">
                {{ c.visitor_display_name }}
              </p>
              <span class="text-[10px] text-slate-400 flex-shrink-0">{{ formatRelative(c.last_message_at ?? c.started_at) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span
                class="text-[10px] font-medium px-1.5 py-0.5 rounded ring-1"
                :class="STATUS_COLOR[c.status]"
              >
                {{ STATUS_LABEL[c.status] }}
              </span>
              <span v-if="c.assigned_agent_name" class="text-[10px] text-slate-400 truncate">
                · {{ c.assigned_agent_name }}
              </span>
            </div>
          </button>

          <div v-if="filteredConversations.length === 0" class="text-center py-12 text-slate-400">
            <UIcon name="i-lucide-inbox" class="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p class="text-xs">Sin conversaciones</p>
          </div>
        </div>
      </div>

      <!-- Chat panel -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">

        <!-- Empty state -->
        <div v-if="!support.activeConversation" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <UIcon name="i-lucide-message-square-text" class="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p class="text-sm text-slate-400">Elegí una conversación de la bandeja</p>
          </div>
        </div>

        <template v-else>
          <!-- Header del chat -->
          <div class="border-b border-slate-100 dark:border-slate-800 px-5 py-3.5 flex items-center justify-between">
            <div>
              <p class="font-semibold text-slate-800 dark:text-slate-100 text-sm">
                {{ support.activeConversation.visitor_display_name }}
              </p>
              <p v-if="support.activeConversation.visitor_email" class="text-xs text-slate-400 font-mono">
                {{ support.activeConversation.visitor_email }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <span
                class="text-[10px] font-medium px-2 py-1 rounded ring-1"
                :class="STATUS_COLOR[support.activeConversation.status]"
              >
                {{ STATUS_LABEL[support.activeConversation.status] }}
              </span>
              <UButton
                v-if="support.activeConversation.status !== 'closed'"
                size="xs"
                variant="ghost"
                color="error"
                icon="i-lucide-x"
                @click="closeChat"
              >Cerrar</UButton>
            </div>
          </div>

          <!-- Mensajes -->
          <div ref="messagesContainer" class="flex-1 overflow-y-auto p-5 space-y-3 bg-slate-50/50 dark:bg-slate-950/30">
            <template v-for="msg in support.messages" :key="msg.id">
              <div v-if="msg.sender === 'agent'" class="flex justify-end">
                <div class="bg-violet-500 text-white rounded-2xl rounded-br-sm px-3 py-2.5 max-w-[70%] shadow-sm">
                  <img v-if="msg.attachment_url" :src="msg.attachment_url" class="rounded-xl max-h-64 object-cover" alt="Adjunto">
                  <p v-if="msg.content" class="text-sm" :class="msg.attachment_url ? 'mt-2 px-1' : 'px-1'">{{ msg.content }}</p>
                  <p class="text-[10px] text-violet-100 mt-1 px-1">{{ formatTime(msg.ts) }}</p>
                </div>
              </div>
              <div v-else-if="msg.sender === 'visitor'" class="flex justify-start">
                <div class="bg-white dark:bg-slate-800 rounded-2xl rounded-bl-sm px-3 py-2.5 max-w-[70%] shadow-sm border border-slate-200 dark:border-slate-700">
                  <img v-if="msg.attachment_url" :src="msg.attachment_url" class="rounded-xl max-h-64 object-cover" alt="Adjunto">
                  <p v-if="msg.content" class="text-sm text-slate-800 dark:text-slate-100" :class="msg.attachment_url ? 'mt-2 px-1' : 'px-1'">{{ msg.content }}</p>
                  <p class="text-[10px] text-slate-400 mt-1 px-1">{{ formatTime(msg.ts) }}</p>
                </div>
              </div>
              <div v-else class="flex justify-center">
                <p class="text-[11px] text-slate-400 italic px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800">
                  {{ msg.content }}
                </p>
              </div>
            </template>
            <div v-if="support.messages.length === 0" class="text-center py-8 text-slate-400">
              <p class="text-xs">Sin mensajes todavía</p>
            </div>
          </div>

          <!-- Quick replies panel (collapsible) -->
          <div
            v-if="support.activeConversation.status !== 'closed' && showQuickReplies"
            class="border-t border-slate-100 dark:border-slate-800 p-3 bg-slate-50/50 max-h-48 overflow-y-auto"
          >
            <p class="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Respuestas rápidas — click para enviar, o doble-click el ícono <UIcon name="i-lucide-pencil" class="w-3 h-3 inline" /> para editar
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              <div
                v-for="qr in QUICK_REPLIES"
                :key="qr"
                class="flex items-center gap-1 group"
              >
                <button
                  type="button"
                  class="flex-1 text-left text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-violet-50 hover:border-violet-300 transition-colors text-slate-700 truncate"
                  :title="qr"
                  @click="sendQuickReply(qr)"
                >
                  {{ qr }}
                </button>
                <button
                  type="button"
                  class="p-1.5 rounded-lg hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Insertar para editar"
                  @click="insertQuickReply(qr)"
                >
                  <UIcon name="i-lucide-pencil" class="w-3 h-3 text-slate-400" />
                </button>
              </div>
            </div>
          </div>

          <!-- Input -->
          <form
            v-if="support.activeConversation.status !== 'closed'"
            class="border-t border-slate-100 dark:border-slate-800 p-3 flex gap-2"
            @submit.prevent="sendMessage"
          >
            <input
              ref="attachInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onAttachmentChange"
            >
            <UButton
              type="button"
              variant="ghost"
              :icon="showQuickReplies ? 'i-lucide-chevron-down' : 'i-lucide-zap'"
              :title="showQuickReplies ? 'Ocultar respuestas rápidas' : 'Respuestas rápidas'"
              @click="showQuickReplies = !showQuickReplies"
            />
            <UButton
              type="button"
              variant="ghost"
              icon="i-lucide-sparkles"
              :loading="aiSuggesting"
              title="Sugerir respuesta con IA"
              @click="suggestWithAI"
            />
            <UButton
              type="button"
              variant="ghost"
              icon="i-lucide-paperclip"
              :loading="uploadingAttachment"
              title="Adjuntar imagen"
              @click="pickAttachment"
            />
            <input
              v-model="inputText"
              type="text"
              placeholder="Escribí un mensaje…"
              class="flex-1 text-sm px-4 py-2.5 rounded-xl border outline-none transition-all border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:border-violet-500"
            >
            <UButton type="submit" :disabled="!inputText.trim()" icon="i-lucide-send">
              Enviar
            </UButton>
          </form>
          <div v-else class="border-t border-slate-100 p-4 text-center">
            <p class="text-xs text-slate-400">Esta conversación está cerrada.</p>
          </div>
        </template>
      </div>
    </div>

    <!-- Close conversation confirmation -->
    <UModal v-model:open="showCloseModal" title="Cerrar conversación">
      <template #content>
        <div class="p-6 space-y-4">
          <div class="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-200">
            <UIcon name="i-lucide-triangle-alert" class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div class="text-sm text-amber-900">
              <p class="font-semibold">¿Cerrar la conversación con {{ support.activeConversation?.visitor_display_name }}?</p>
              <p class="mt-1 text-amber-800">
                El visitante recibirá un aviso de que la conversación fue cerrada. No podrás
                seguir respondiendo desde acá; si vuelve, se abrirá una conversación nueva.
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2 border-t" style="border-color: #F3F4F6;">
            <UButton variant="ghost" color="neutral" @click="showCloseModal = false">
              Volver
            </UButton>
            <UButton
              color="error"
              :loading="closing"
              icon="i-lucide-x"
              @click="confirmCloseChat"
            >
              Sí, cerrar conversación
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
