import { defineStore } from 'pinia'

export type ChatRole = 'user' | 'bot' | 'agent' | 'system'

export interface ChatMessage {
  role: ChatRole
  content: string
  ts?: string
  showMenuAfter?: boolean
  showEscalateButton?: boolean
  attachmentUrl?: string | null
}

const STORAGE_KEY = 'agendamiento:chat'

interface WSMessage {
  type: 'ready' | 'message' | 'status' | 'error'
  conversation_id?: string
  status?: string
  agent_name?: string
  agent_avatar_url?: string | null
  closed_by?: string
  id?: string
  sender?: 'visitor' | 'agent' | 'system' | 'ai'
  content?: string
  attachment_url?: string | null
  ts?: string
  message?: string
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    conversationId: null as string | null,
    wsStatus: 'idle' as 'idle' | 'connecting' | 'connected' | 'disconnected',
    agentName: null as string | null,
    agentAvatarUrl: null as string | null,
    chatStatus: 'idle' as 'idle' | 'open' | 'assigned' | 'closed',
    _socket: null as WebSocket | null
  }),

  actions: {
    hydrate() {
      if (!import.meta.client) return
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) return
        const data = JSON.parse(raw)
        this.messages = Array.isArray(data.messages) ? data.messages : []
        this.conversationId = data.conversationId ?? null
        this.chatStatus = data.chatStatus ?? 'idle'
        this.agentName = data.agentName ?? null
      }
      catch {
        // corrupted storage — ignore
      }
    },

    persist() {
      if (!import.meta.client) return
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          messages: this.messages,
          conversationId: this.conversationId,
          chatStatus: this.chatStatus,
          agentName: this.agentName
        }))
      }
      catch {
        // ignore
      }
    },

    addMessage(msg: ChatMessage) {
      this.messages.push({ ...msg, ts: msg.ts ?? new Date().toISOString() })
      this.persist()
    },

    /**
     * Open a websocket as a public visitor and ask to talk to a human agent.
     * Sends 'start' once connected. Returns a Promise that resolves on 'ready'.
     */
    async startHumanChat(opts: { tenantSlug: string; visitorName?: string; visitorEmail?: string }) {
      if (!import.meta.client) return
      if (this.wsStatus === 'connected' || this.wsStatus === 'connecting') return

      const config = useRuntimeConfig()
      const apiBase = (config.public.apiBase as string).replace(/\/rest\/v1\/?$/, '')
      const wsBase = apiBase.replace(/^http/, 'ws')
      const url = `${wsBase}/ws/support/visitor/?tenant=${encodeURIComponent(opts.tenantSlug)}`

      this.wsStatus = 'connecting'
      const ws = new WebSocket(url)
      this._socket = ws

      ws.onopen = () => {
        this.wsStatus = 'connected'
        ws.send(JSON.stringify({
          type: 'start',
          name: opts.visitorName ?? '',
          email: opts.visitorEmail ?? ''
        }))
      }

      ws.onmessage = (ev) => {
        let data: WSMessage
        try { data = JSON.parse(ev.data) }
        catch { return }
        this._handleWSMessage(data)
      }

      ws.onclose = () => {
        this.wsStatus = 'disconnected'
        this._socket = null
      }

      ws.onerror = () => {
        this.wsStatus = 'disconnected'
      }
    },

    sendChatMessage(text: string) {
      if (!this._socket || this.wsStatus !== 'connected') return false
      this._socket.send(JSON.stringify({ type: 'message', content: text }))
      return true
    },

    _handleWSMessage(data: WSMessage) {
      if (data.type === 'ready' && data.conversation_id) {
        this.conversationId = data.conversation_id
        this.chatStatus = (data.status as 'open' | 'assigned') ?? 'open'
        this.persist()
        return
      }
      if (data.type === 'status') {
        this.chatStatus = (data.status as 'open' | 'assigned' | 'closed') ?? this.chatStatus
        if (data.agent_name) this.agentName = data.agent_name
        if (data.agent_avatar_url !== undefined) this.agentAvatarUrl = data.agent_avatar_url
        this.persist()
        return
      }
      if (data.type === 'message') {
        // No mostrar el eco de los mensajes del visitante (ya están)
        if (data.sender === 'visitor') return
        const role: ChatRole = data.sender === 'agent' ? 'agent' : 'system'
        this.addMessage({
          role,
          content: data.content ?? '',
          attachmentUrl: data.attachment_url ?? null,
          ts: data.ts
        })
      }
    },

    closeChat() {
      // Avisar al backend (que avise al agente) ANTES de cerrar el socket.
      if (this._socket && this.wsStatus === 'connected') {
        try { this._socket.send(JSON.stringify({ type: 'close' })) }
        catch { /* ignore */ }
      }
      // Damos un instante para que el mensaje salga, luego cerramos
      setTimeout(() => {
        if (this._socket) {
          try { this._socket.close() }
          catch { /* ignore */ }
        }
        this._socket = null
        this.wsStatus = 'idle'
      }, 100)
      this.chatStatus = 'closed'
      this.persist()
    },

    clear() {
      this.closeChat()
      this.messages = []
      this.conversationId = null
      this.chatStatus = 'idle'
      this.agentName = null
      if (import.meta.client) {
        localStorage.removeItem(STORAGE_KEY)
      }
    }
  }
})
