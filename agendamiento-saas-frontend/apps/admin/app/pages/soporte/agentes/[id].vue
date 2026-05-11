<script setup lang="ts">
definePageMeta({ middleware: ['tenant', 'auth'] })

const route = useRoute()
const { apiFetch } = useApi()

interface Conversation {
  id: string
  title: string
  visitor_display_name: string
  visitor_name: string
  visitor_email: string
  status: 'open' | 'assigned' | 'closed'
  started_at: string
  closed_at: string | null
  last_message_at: string | null
  message_count: number
}

interface Message {
  id: string
  sender: 'visitor' | 'agent' | 'system' | 'ai'
  content: string
  created_at: string
}

interface SupportAgent {
  user_id: number
  email: string
  full_name: string
  role: string
  is_online: boolean
  total_conversations: number
  open_conversations: number
  closed_conversations: number
  last_active: string | null
}

const agentId = computed(() => Number(route.params.id))
const agent = ref<SupportAgent | null>(null)
const conversations = ref<Conversation[]>([])
const selectedId = ref<string | null>(null)
const messages = ref<Message[]>([])
const loading = ref(false)
const loadingDetail = ref(false)

const STATUS_LABEL = { open: 'Esperando', assigned: 'Activa', closed: 'Cerrada' }
const STATUS_COLOR = {
  open: 'bg-amber-100 text-amber-700 ring-amber-200',
  assigned: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
  closed: 'bg-slate-100 text-slate-600 ring-slate-200'
}

async function loadAgent() {
  loading.value = true
  try {
    const [agents, convs] = await Promise.all([
      apiFetch<SupportAgent[] | { results: SupportAgent[] }>('/support/agents/'),
      apiFetch<Conversation[] | { results: Conversation[] }>('/support/conversations/', {
        params: { agent: String(agentId.value) }
      })
    ])
    const list = Array.isArray(agents) ? agents : agents.results
    agent.value = list.find(a => a.user_id === agentId.value) ?? null
    conversations.value = Array.isArray(convs) ? convs : convs.results
  } finally {
    loading.value = false
  }
}

async function loadConversation(id: string) {
  selectedId.value = id
  loadingDetail.value = true
  try {
    const res = await apiFetch<{ messages: Message[] }>(`/support/conversations/${id}/`)
    messages.value = res.messages ?? []
  } finally {
    loadingDetail.value = false
  }
}

const selectedConversation = computed(() =>
  conversations.value.find(c => c.id === selectedId.value)
)

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('es-MX', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadAgent)
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center gap-3">
      <UButton variant="ghost" icon="i-lucide-arrow-left" size="sm" to="/soporte/agentes">Volver</UButton>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-violet-500" />
    </div>

    <template v-else-if="agent">
      <!-- Agent header -->
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
        <div class="flex items-start gap-4">
          <div class="w-16 h-16 rounded-full bg-violet-100 flex items-center justify-center text-2xl font-bold text-violet-700 uppercase ring-2 ring-white shadow-sm">
            {{ agent.full_name[0] }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h1 class="text-xl font-bold text-slate-900 dark:text-white truncate">{{ agent.full_name }}</h1>
              <span
                class="text-[10px] font-medium px-2 py-1 rounded ring-1 inline-flex items-center gap-1"
                :class="agent.is_online
                  ? 'bg-emerald-100 text-emerald-700 ring-emerald-200'
                  : 'bg-slate-100 text-slate-500 ring-slate-200'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="agent.is_online ? 'bg-emerald-500' : 'bg-slate-400'" />
                {{ agent.is_online ? 'En línea' : 'Offline' }}
              </span>
            </div>
            <p class="text-sm text-slate-400">{{ agent.email }}</p>
          </div>

          <div class="flex gap-6 text-center">
            <div>
              <p class="text-2xl font-bold text-slate-800">{{ agent.total_conversations }}</p>
              <p class="text-[10px] text-slate-400 uppercase tracking-wide">Total</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-emerald-600">{{ agent.open_conversations }}</p>
              <p class="text-[10px] text-slate-400 uppercase tracking-wide">Activas</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-slate-500">{{ agent.closed_conversations }}</p>
              <p class="text-[10px] text-slate-400 uppercase tracking-wide">Cerradas</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Conversations + chat detail (split layout) -->
      <div class="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4 h-[calc(100vh-330px)] min-h-[500px]">

        <!-- List -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
          <div class="border-b border-slate-100 dark:border-slate-800 px-4 py-3">
            <p class="font-semibold text-sm text-slate-700">Conversaciones atendidas</p>
          </div>

          <div class="flex-1 overflow-y-auto">
            <button
              v-for="c in conversations"
              :key="c.id"
              type="button"
              class="w-full text-left px-4 py-3.5 border-b border-slate-100 dark:border-slate-800 transition-colors"
              :class="selectedId === c.id
                ? 'bg-violet-50 dark:bg-violet-900/20'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'"
              @click="loadConversation(c.id)"
            >
              <div class="flex items-start justify-between gap-2 mb-1.5">
                <p class="font-semibold text-sm text-slate-800 truncate">
                  {{ c.title || c.visitor_display_name }}
                </p>
                <span
                  class="text-[10px] font-medium px-1.5 py-0.5 rounded ring-1 flex-shrink-0"
                  :class="STATUS_COLOR[c.status]"
                >
                  {{ STATUS_LABEL[c.status] }}
                </span>
              </div>
              <p v-if="c.title" class="text-[11px] text-slate-400 mb-1 truncate">
                con {{ c.visitor_display_name }}
              </p>
              <div class="flex items-center gap-3 text-[11px] text-slate-400">
                <span>{{ formatDateTime(c.started_at) }}</span>
                <span class="inline-flex items-center gap-1">
                  <UIcon name="i-lucide-message-square" class="w-3 h-3" />
                  {{ c.message_count }}
                </span>
              </div>
            </button>

            <div v-if="conversations.length === 0" class="text-center py-12 text-slate-400">
              <UIcon name="i-lucide-inbox" class="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p class="text-xs">Este agente no atendió conversaciones todavía</p>
            </div>
          </div>
        </div>

        <!-- Detail -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">

          <div v-if="!selectedConversation" class="flex-1 flex items-center justify-center">
            <div class="text-center">
              <UIcon name="i-lucide-message-square-text" class="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p class="text-sm text-slate-400">Elegí una conversación de la lista</p>
            </div>
          </div>

          <template v-else>
            <div class="border-b border-slate-100 dark:border-slate-800 px-5 py-3.5">
              <p class="font-semibold text-slate-800">{{ selectedConversation.title || selectedConversation.visitor_display_name }}</p>
              <p class="text-xs text-slate-400 mt-0.5">
                con <strong>{{ selectedConversation.visitor_display_name }}</strong>
                <span v-if="selectedConversation.visitor_email"> · {{ selectedConversation.visitor_email }}</span>
                · {{ formatDateTime(selectedConversation.started_at) }}
              </p>
            </div>

            <div class="flex-1 overflow-y-auto p-5 space-y-3 bg-slate-50/50 dark:bg-slate-950/30">
              <div v-if="loadingDetail" class="flex justify-center py-12">
                <UIcon name="i-lucide-loader-2" class="animate-spin w-6 h-6 text-violet-500" />
              </div>
              <template v-else>
                <template v-for="msg in messages" :key="msg.id">
                  <div v-if="msg.sender === 'agent'" class="flex justify-end">
                    <div class="bg-violet-500 text-white rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[70%] shadow-sm">
                      <p class="text-sm">{{ msg.content }}</p>
                      <p class="text-[10px] text-violet-100 mt-1">{{ formatTime(msg.created_at) }}</p>
                    </div>
                  </div>
                  <div v-else-if="msg.sender === 'visitor'" class="flex justify-start">
                    <div class="bg-white dark:bg-slate-800 rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[70%] shadow-sm border border-slate-200">
                      <p class="text-sm text-slate-800">{{ msg.content }}</p>
                      <p class="text-[10px] text-slate-400 mt-1">{{ formatTime(msg.created_at) }}</p>
                    </div>
                  </div>
                  <div v-else class="flex justify-center">
                    <p class="text-[11px] text-slate-400 italic px-3 py-1 rounded-full bg-slate-100">
                      {{ msg.content }}
                    </p>
                  </div>
                </template>
                <div v-if="messages.length === 0" class="text-center py-8 text-slate-400">
                  <p class="text-xs">Sin mensajes</p>
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>
