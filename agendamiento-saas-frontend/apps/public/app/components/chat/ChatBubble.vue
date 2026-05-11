<script setup lang="ts">
import { useChatStore } from '~/stores/chat'

const chat = useChatStore()
const tenant = useTenantStore()

const open = ref(false)
const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const planFlags = computed(() => tenant.tenant?.plan_flags ?? {})
const hasHumanSupport = computed(() => !!planFlags.value.chat_human_support)
const hasAISupport = computed(() => !!planFlags.value.chat_ai_support)

// FAQ canned responses — locales (no van al backend en Fase 1)
interface FAQOption {
  id: string
  label: string
  answer: string
}

const FAQ_OPTIONS: FAQOption[] = [
  {
    id: 'how-to-book',
    label: '¿Cómo agendo una cita?',
    answer: 'Es muy fácil. Andá a la sección "Agendar cita", elegí un doctor, un servicio y la fecha. Te mostraremos los horarios disponibles y podés reservar en menos de un minuto. Si necesitás ayuda, podés escribirnos en este chat.'
  },
  {
    id: 'hours',
    label: 'Horarios de atención',
    answer: 'Nuestros horarios varían según el doctor. Cuando entres a "Agendar", al elegir un doctor verás todos sus días y horas disponibles. La mayoría atiende de lunes a viernes en horario diurno.'
  },
  {
    id: 'services',
    label: '¿Qué servicios ofrecen?',
    answer: 'Tenemos consultas con varios doctores especialistas. Podés ver el listado completo en la sección "Servicios" del menú principal o directamente en el wizard de agendar.'
  },
  {
    id: 'cancel',
    label: '¿Puedo cancelar una cita?',
    answer: 'Sí. Recibirás un correo de confirmación con los detalles de tu cita. Si necesitás cancelarla o reagendarla, contactanos por este chat o respondé al correo.'
  },
  {
    id: 'payment',
    label: 'Métodos de pago',
    answer: 'El pago se realiza directamente en el consultorio el día de la cita. Aceptamos efectivo, tarjeta y transferencia.'
  }
]

function selectOption(opt: FAQOption) {
  chat.addMessage({ role: 'user', content: opt.label })
  setTimeout(() => {
    chat.addMessage({ role: 'bot', content: opt.answer, showMenuAfter: true })
    scrollToBottom()
  }, 300)
}

const showVisitorForm = ref(false)
const visitorName = ref('')
const visitorEmail = ref('')

const isInHumanChat = computed(() => chat.chatStatus === 'open' || chat.chatStatus === 'assigned')
const isHumanChatClosed = computed(() => chat.chatStatus === 'closed')

const aiThinking = ref(false)
const { apiFetch } = useApi()

async function sendFreeText() {
  const text = inputText.value.trim()
  if (!text) return
  chat.addMessage({ role: 'user', content: text })
  const messageToSend = text
  inputText.value = ''

  // Caso 1 — chat humano activo: SIEMPRE mandamos al WS (nunca a la IA).
  // Si el WS no está conectado, avisamos al usuario en vez de fallback a IA,
  // porque la IA respondería sin el contexto del agente y se mezclarían las dos voces.
  if (isInHumanChat.value) {
    if (chat.wsStatus === 'connected') {
      chat.sendChatMessage(messageToSend)
    } else {
      chat.addMessage({
        role: 'system',
        content: 'No se pudo enviar el mensaje. La conexión con el agente está caída — recargá la página o iniciá un chat nuevo.'
      })
    }
    scrollToBottom()
    return
  }

  // Caso 2 — plan con IA: pedirle respuesta a Ollama
  if (hasAISupport.value) {
    aiThinking.value = true
    scrollToBottom()
    try {
      const history = chat.messages
        .filter(m => m.role === 'user' || m.role === 'bot')
        .slice(-8)
        .map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.content }))

      const res = await apiFetch<{ reply: string; should_escalate: boolean; feature_gated?: boolean }>(
        '/public/ai/chat/',
        { method: 'POST', body: { message: messageToSend, history } }
      )

      if (res.feature_gated) {
        chat.addMessage({
          role: 'bot',
          content: 'La asistencia con IA no está disponible en este plan. Probá las opciones del menú.',
          showMenuAfter: true
        })
      } else {
        chat.addMessage({
          role: 'bot',
          content: res.reply,
          showEscalateButton: res.should_escalate && hasHumanSupport.value
        })
      }
    } catch {
      chat.addMessage({
        role: 'bot',
        content: hasHumanSupport.value
          ? 'Hubo un problema procesando tu mensaje. Probá de nuevo o apretá "Hablar con un agente humano".'
          : 'Hubo un problema procesando tu mensaje. Probá de nuevo o usá el menú de opciones.',
        showMenuAfter: true
      })
    } finally {
      aiThinking.value = false
      scrollToBottom()
    }
    return
  }

  // Caso 3 — plan sin IA ni chat humano abierto: fallback canned
  setTimeout(() => {
    const fallback = hasHumanSupport.value
      ? 'Por ahora puedo ayudarte con las opciones del menú. Si necesitás hablar con alguien, apretá "Hablar con un agente humano".'
      : 'Te puedo ayudar con las opciones del menú. Para consultas más específicas, podés contactarnos por los canales de la sección Contacto.'
    chat.addMessage({
      role: 'bot',
      content: fallback,
      showMenuAfter: true
    })
    scrollToBottom()
  }, 400)
}

function requestHuman() {
  // Mostrar mini-form para que el usuario diga su nombre — opcional
  showVisitorForm.value = true
}

async function startHumanChat() {
  const slug = tenant.tenant?.slug
  if (!slug) return
  showVisitorForm.value = false
  chat.addMessage({ role: 'user', content: 'Quiero hablar con alguien' })
  scrollToBottom()
  await chat.startHumanChat({
    tenantSlug: slug,
    visitorName: visitorName.value.trim(),
    visitorEmail: visitorEmail.value.trim()
  })
  scrollToBottom()
}

function endHumanChat() {
  if (chat.chatStatus === 'closed') return  // ya estaba cerrado, evitar dobles
  chat.closeChat()
  chat.addMessage({
    role: 'system',
    content: 'Cerraste el chat con el agente. La conversación quedó archivada.'
  })
}

const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

function pickAttachment() {
  fileInput.value?.click()
}

async function onAttachmentChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!chat.conversationId) {
    inputText.value = '[Iniciá un chat con un agente para enviar imágenes]'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    chat.addMessage({ role: 'system', content: 'La imagen no puede pesar más de 10 MB.' })
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('image', file)
    fd.append('sender', 'visitor')
    const config = useRuntimeConfig()
    const url = `${config.public.apiBase}/support/conversations/${chat.conversationId}/upload-attachment/`
    const res = await fetch(url, { method: 'POST', body: fd })
    if (!res.ok) throw new Error()
    const data = await res.json()
    // Mostrar localmente del lado del visitante (el agente lo recibe via WS broadcast)
    chat.addMessage({
      role: 'user',
      content: '',
      attachmentUrl: data.attachment_url ?? null
    })
  }
  catch {
    chat.addMessage({ role: 'system', content: 'No se pudo subir la imagen.' })
  }
  finally {
    uploading.value = false
    if (input) input.value = ''
  }
}

function startNewChat() {
  // Limpia toda la conversación previa para empezar de cero
  chat.clear()
  inputText.value = ''
  showVisitorForm.value = false
  visitorName.value = ''
  visitorEmail.value = ''
}

function clearChat() {
  chat.clear()
  open.value = false
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

watch(open, (val) => {
  if (val) scrollToBottom()
})

// Cada mensaje nuevo (entrante o saliente) — auto-scroll al final
watch(() => chat.messages.length, () => { scrollToBottom() })

// Cuando el indicador "..." aparece o desaparece, también scroll
watch(aiThinking, () => { scrollToBottom() })

onMounted(() => {
  chat.hydrate()
})
</script>

<template>
  <!-- Floating bubble button (always visible) -->
  <button
    v-if="!open"
    type="button"
    class="fixed bottom-5 right-5 z-50 w-14 h-14 rounded-full bg-sage-500 hover:bg-sage-600 shadow-lg hover:shadow-xl transition-all flex items-center justify-center group"
    aria-label="Abrir chat"
    @click="open = true"
  >
    <UIcon name="i-lucide-message-circle" class="w-6 h-6 text-white" />
    <span
      v-if="chat.messages.length > 0"
      class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center border-2 border-white"
    >
      {{ chat.messages.filter(m => m.role === 'bot').length }}
    </span>
  </button>

  <!-- Chat window -->
  <Transition
    enter-active-class="transition-all duration-200 ease-out"
    enter-from-class="opacity-0 scale-95 translate-y-2"
    enter-to-class="opacity-100 scale-100 translate-y-0"
    leave-active-class="transition-all duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="open"
      class="fixed bottom-5 right-5 z-50 w-[380px] max-w-[calc(100vw-2rem)] h-[560px] max-h-[calc(100vh-3rem)] bg-white rounded-2xl shadow-2xl border border-border flex flex-col overflow-hidden"
    >
      <!-- Header -->
      <div class="bg-gradient-to-br from-sage-500 to-sage-600 px-5 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center ring-2 ring-white/30 overflow-hidden">
            <img
              v-if="(isInHumanChat || isHumanChatClosed) && chat.agentAvatarUrl"
              :src="chat.agentAvatarUrl"
              :alt="chat.agentName ?? ''"
              class="w-full h-full object-cover"
            >
            <UIcon v-else name="i-lucide-message-circle" class="w-5 h-5 text-white" />
          </div>
          <div>
            <p class="font-semibold text-white text-sm leading-tight">
              <template v-if="(isInHumanChat || isHumanChatClosed) && chat.agentName">{{ chat.agentName }}</template>
              <template v-else>{{ tenant.tenant?.name ?? 'Asistente' }}</template>
            </p>
            <p class="text-[11px] text-white/80 mt-0.5 inline-flex items-center gap-1">
              <span
                class="w-1.5 h-1.5 rounded-full"
                :class="isHumanChatClosed ? 'bg-slate-300' : 'bg-emerald-300'"
              />
              <template v-if="chat.chatStatus === 'open'">Conectando con un agente…</template>
              <template v-else-if="chat.chatStatus === 'assigned'">Agente en línea</template>
              <template v-else-if="isHumanChatClosed">Sesión cerrada</template>
              <template v-else>En línea</template>
            </p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button
            v-if="chat.messages.length > 0"
            type="button"
            class="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
            title="Limpiar conversación"
            @click="clearChat"
          >
            <UIcon name="i-lucide-rotate-ccw" class="w-4 h-4 text-white/80" />
          </button>
          <button
            type="button"
            class="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="Cerrar chat"
            @click="open = false"
          >
            <UIcon name="i-lucide-x" class="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3 bg-[#FAFBFA]">
        <!-- Welcome message + initial menu -->
        <template v-if="chat.messages.length === 0">
          <div class="flex gap-2 items-end">
            <div class="w-7 h-7 rounded-full bg-sage-100 flex items-center justify-center flex-shrink-0">
              <UIcon name="i-lucide-sparkles" class="w-3.5 h-3.5 text-sage-600" />
            </div>
            <div class="bg-white rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%] shadow-sm border border-border">
              <p class="text-sm text-ink">
                <template v-if="hasAISupport">
                  ¡Hola! 👋 Soy el asistente IA de <strong>{{ tenant.tenant?.name }}</strong>.
                  Contame en qué te puedo ayudar y respondo al instante. Si preferís hablar con
                  una persona, decime "quiero hablar con un agente humano".
                </template>
                <template v-else>
                  ¡Hola! 👋 Soy el asistente de <strong>{{ tenant.tenant?.name }}</strong>.
                  ¿En qué te puedo ayudar?
                </template>
              </p>
            </div>
          </div>
          <!-- Menú de opciones SOLO si no hay IA (para planes free / starter) -->
          <div v-if="!hasAISupport" class="space-y-2 pl-9 pt-1">
            <button
              v-for="opt in FAQ_OPTIONS"
              :key="opt.id"
              type="button"
              class="w-full text-left text-sm px-3.5 py-2.5 rounded-xl border border-sage-200 bg-white hover:bg-sage-50 hover:border-sage-300 transition-colors text-sage-700"
              @click="selectOption(opt)"
            >
              {{ opt.label }}
            </button>
            <button
              v-if="hasHumanSupport"
              type="button"
              class="w-full text-left text-sm px-3.5 py-2.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 transition-colors text-rose-700 font-medium inline-flex items-center gap-2"
              @click="requestHuman"
            >
              <UIcon name="i-lucide-user-round" class="w-4 h-4" />
              Hablar con un agente humano
            </button>
          </div>
        </template>

        <!-- Message thread -->
        <template v-for="(msg, i) in chat.messages" :key="i">
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="bg-sage-500 text-white rounded-2xl rounded-br-sm px-3 py-2.5 max-w-[80%] shadow-sm">
              <img
                v-if="msg.attachmentUrl"
                :src="msg.attachmentUrl"
                class="rounded-xl max-h-56 object-cover"
                alt="Adjunto"
              >
              <p v-if="msg.content" class="text-sm" :class="msg.attachmentUrl ? 'mt-2' : ''">{{ msg.content }}</p>
            </div>
          </div>
          <div v-else class="space-y-2">
            <div class="flex gap-2 items-end">
              <div
                class="w-7 h-7 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0"
                :class="msg.role === 'agent' ? 'bg-rose-100' : msg.role === 'system' ? 'bg-slate-100' : 'bg-sage-100'"
              >
                <img
                  v-if="msg.role === 'agent' && chat.agentAvatarUrl"
                  :src="chat.agentAvatarUrl"
                  :alt="chat.agentName ?? ''"
                  class="w-full h-full object-cover"
                >
                <UIcon
                  v-else
                  :name="msg.role === 'agent' ? 'i-lucide-user-round' : msg.role === 'system' ? 'i-lucide-info' : 'i-lucide-sparkles'"
                  class="w-3.5 h-3.5"
                  :class="msg.role === 'agent' ? 'text-rose-600' : msg.role === 'system' ? 'text-slate-500' : 'text-sage-600'"
                />
              </div>
              <div
                class="rounded-2xl rounded-bl-sm px-3 py-2.5 max-w-[80%] shadow-sm border"
                :class="msg.role === 'system' ? 'bg-slate-50 border-slate-200' : 'bg-white border-border'"
              >
                <img
                  v-if="msg.attachmentUrl"
                  :src="msg.attachmentUrl"
                  class="rounded-xl max-h-56 object-cover"
                  alt="Adjunto"
                >
                <p v-if="msg.content" class="text-sm text-ink whitespace-pre-line" :class="msg.attachmentUrl ? 'mt-2 px-1' : 'px-1'">{{ msg.content }}</p>
              </div>
            </div>
            <!-- Botón inline de escalación a humano (modo IA) -->
            <div
              v-if="msg.showEscalateButton && i === chat.messages.length - 1 && !isInHumanChat"
              class="pl-9 pt-1"
            >
              <button
                type="button"
                class="text-sm font-medium px-3.5 py-2.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 transition-colors text-rose-700 inline-flex items-center gap-2"
                @click="requestHuman"
              >
                <UIcon name="i-lucide-user-round" class="w-4 h-4" />
                Sí, conectarme con un humano
              </button>
            </div>
            <div v-if="msg.showMenuAfter && i === chat.messages.length - 1 && !isInHumanChat && !aiThinking && !hasAISupport" class="space-y-2 pl-9 pt-1">
              <p class="text-[11px] text-ink-muted font-medium uppercase tracking-wide mb-1.5">Otras opciones</p>
              <button
                v-for="opt in FAQ_OPTIONS"
                :key="opt.id"
                type="button"
                class="w-full text-left text-sm px-3.5 py-2.5 rounded-xl border border-sage-200 bg-white hover:bg-sage-50 hover:border-sage-300 transition-colors text-sage-700"
                @click="selectOption(opt)"
              >
                {{ opt.label }}
              </button>
              <button
                v-if="hasHumanSupport"
                type="button"
                class="w-full text-left text-sm px-3.5 py-2.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 transition-colors text-rose-700 font-medium inline-flex items-center gap-2"
                @click="requestHuman"
              >
                <UIcon name="i-lucide-user-round" class="w-4 h-4" />
                Hablar con un agente humano
              </button>
            </div>
          </div>
        </template>

        <!-- AI thinking indicator (al final, debajo del último mensaje) -->
        <div v-if="aiThinking" class="flex gap-2 items-end">
          <div class="w-7 h-7 rounded-full bg-sage-100 flex items-center justify-center flex-shrink-0">
            <UIcon name="i-lucide-sparkles" class="w-3.5 h-3.5 text-sage-600" />
          </div>
          <div class="bg-white rounded-2xl rounded-bl-sm px-4 py-2.5 shadow-sm border border-border">
            <div class="flex gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-sage-400 animate-bounce" style="animation-delay: 0ms" />
              <span class="w-1.5 h-1.5 rounded-full bg-sage-400 animate-bounce" style="animation-delay: 150ms" />
              <span class="w-1.5 h-1.5 rounded-full bg-sage-400 animate-bounce" style="animation-delay: 300ms" />
            </div>
          </div>
        </div>
      </div>

      <!-- Mini-form de visitante antes de conectar con humano -->
      <div v-if="showVisitorForm" class="border-t border-border p-4 bg-white space-y-3">
        <p class="text-sm font-medium text-ink">Antes de conectarte, contanos quién sos:</p>
        <input
          v-model="visitorName"
          type="text"
          placeholder="Tu nombre (opcional)"
          class="w-full text-sm px-3.5 py-2 rounded-lg border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
        >
        <input
          v-model="visitorEmail"
          type="email"
          placeholder="Tu email (opcional)"
          class="w-full text-sm px-3.5 py-2 rounded-lg border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
        >
        <div class="flex gap-2">
          <button
            type="button"
            class="flex-1 text-sm font-medium px-3 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition-colors"
            @click="startHumanChat"
          >
            Conectarme
          </button>
          <button
            type="button"
            class="text-sm px-3 py-2 rounded-lg text-ink-soft hover:bg-page-alt transition-colors"
            @click="showVisitorForm = false"
          >
            Cancelar
          </button>
        </div>
      </div>

      <!-- Banner de chat cerrado -->
      <div v-else-if="isHumanChatClosed" class="border-t border-border p-4 bg-slate-50">
        <div class="flex items-start gap-3 mb-3">
          <UIcon name="i-lucide-circle-check" class="w-5 h-5 text-sage-600 flex-shrink-0 mt-0.5" />
          <div class="flex-1 text-sm">
            <p class="font-semibold text-ink">Sesión cerrada</p>
            <p class="text-ink-muted text-xs mt-0.5">
              La conversación con el agente terminó. Para hablar de nuevo, iniciá un chat nuevo.
            </p>
          </div>
        </div>
        <button
          type="button"
          class="w-full text-sm font-medium px-4 py-2.5 rounded-xl bg-sage-500 hover:bg-sage-600 text-white transition-colors inline-flex items-center justify-center gap-2"
          @click="startNewChat"
        >
          <UIcon name="i-lucide-rotate-ccw" class="w-4 h-4" />
          Iniciar un nuevo chat
        </button>
      </div>

      <!-- Input principal -->
      <div v-else class="border-t border-border p-3 bg-white">
        <div v-if="isInHumanChat" class="flex items-center justify-between mb-2 px-1">
          <span class="text-[11px] font-medium text-ink-muted uppercase tracking-wide">
            <template v-if="chat.chatStatus === 'open'">Esperando agente…</template>
            <template v-else-if="chat.chatStatus === 'assigned'">Hablando con {{ chat.agentName }}</template>
          </span>
          <button
            type="button"
            class="text-[11px] text-rose-500 hover:underline"
            @click="endHumanChat"
          >
            Cerrar chat
          </button>
        </div>
        <form class="flex gap-2 items-end" @submit.prevent="sendFreeText">
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onAttachmentChange"
          >
          <button
            v-if="isInHumanChat"
            type="button"
            :disabled="uploading"
            class="p-2.5 rounded-xl transition-colors text-ink-soft hover:bg-page-alt disabled:opacity-40"
            aria-label="Adjuntar imagen"
            title="Adjuntar imagen"
            @click="pickAttachment"
          >
            <UIcon :name="uploading ? 'i-lucide-loader-2' : 'i-lucide-paperclip'" class="w-4 h-4" :class="uploading ? 'animate-spin' : ''" />
          </button>
          <input
            v-model="inputText"
            type="text"
            :placeholder="isInHumanChat ? 'Escribí tu mensaje…' : 'Escribí tu mensaje o elegí del menú…'"
            class="flex-1 text-sm px-3.5 py-2.5 rounded-xl border outline-none transition-all border-border-strong bg-white text-ink focus:border-sage-500"
          >
          <button
            type="submit"
            :disabled="!inputText.trim()"
            class="p-2.5 rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed bg-sage-500 hover:bg-sage-600 text-white"
            aria-label="Enviar"
          >
            <UIcon name="i-lucide-send" class="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  </Transition>
</template>
