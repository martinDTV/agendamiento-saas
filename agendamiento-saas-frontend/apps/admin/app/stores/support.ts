import { defineStore } from 'pinia'

export type AgentMessageSender = 'visitor' | 'agent' | 'system' | 'ai'

export interface AgentMessage {
  id: string
  sender: AgentMessageSender
  content: string
  attachment_url?: string | null
  ts: string
}

export interface AgentConversation {
  id: string
  visitor_name: string
  visitor_email: string
  visitor_display_name: string
  status: 'open' | 'assigned' | 'closed'
  assigned_agent: number | null
  assigned_agent_name: string | null
  started_at: string
  last_message_at: string | null
}

interface WSEvent {
  type: 'ready' | 'opened' | 'message' | 'status' | 'inbox' | 'error'
  event?: 'new_conversation'
  conversation_id?: string
  visitor_name?: string
  started_at?: string
  status?: string
  closed_by?: 'visitor' | 'agent'
  agent_name?: string
  id?: string
  sender?: AgentMessageSender
  content?: string
  attachment_url?: string | null
  ts?: string
  message?: string
}

export const useSupportStore = defineStore('support', {
  state: () => ({
    conversations: [] as AgentConversation[],
    activeId: null as string | null,
    messages: [] as AgentMessage[],
    wsStatus: 'idle' as 'idle' | 'connecting' | 'connected' | 'disconnected',
    _socket: null as WebSocket | null
  }),

  getters: {
    activeConversation(state): AgentConversation | undefined {
      return state.conversations.find(c => c.id === state.activeId)
    }
  },

  actions: {
    async fetchConversations(statusFilter?: 'open' | 'assigned' | 'closed') {
      const { $api } = useNuxtApp()
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter
      const res = await $api.get<{ results: AgentConversation[] } | AgentConversation[]>(
        '/support/conversations/', { params }
      )
      this.conversations = Array.isArray(res.data) ? res.data : res.data.results
    },

    async openConversation(id: string) {
      const { $api } = useNuxtApp()
      this.activeId = id
      const res = await $api.get<{ messages: AgentMessage[] }>(`/support/conversations/${id}/`)
      this.messages = res.data.messages ?? []

      // Forzar conexión saludable antes de subscribir
      this._ensureWS()
      await this._sendOpenWhenReady(id)
    },

    /**
     * Garantiza que haya un WebSocket abierto. Si está cerrado o el state interno
     * está stale, reconecta. Llamar antes de cualquier op crítica.
     */
    _ensureWS() {
      const tenant = useTenantStore()
      if (!tenant.slug) return
      const sock = this._socket
      const isHealthy = sock && sock.readyState === WebSocket.OPEN
      if (isHealthy) return

      // Socket muerto (cerrado, cerrándose, o nunca conectó). Limpiar state y reconectar.
      if (sock) {
        try { sock.close() }
        catch { /* ignore */ }
      }
      this._socket = null
      this.wsStatus = 'idle'
      console.log('[support] _ensureWS: reconnecting (socket was', sock ? sock.readyState : 'null', ')')
      this.connectWS(tenant.slug)
    },

    async _sendOpenWhenReady(id: string, attempts = 20) {
      for (let i = 0; i < attempts; i++) {
        const sock = this._socket
        if (sock && sock.readyState === WebSocket.OPEN) {
          sock.send(JSON.stringify({ type: 'open', conversation_id: id }))
          console.log('[support] sent open for conv', id)
          return
        }
        // Si pasaron 1.5s y seguimos sin socket OPEN, forzar otro reconnect
        if (i === 8 && (!sock || sock.readyState === WebSocket.CLOSED)) {
          console.log('[support] socket still not open, forcing reconnect')
          this._ensureWS()
        }
        await new Promise(r => setTimeout(r, 200))
      }
      console.warn('[support] WS never became connected; conversation not subscribed live')
    },

    connectWS(tenantSlug: string) {
      if (!import.meta.client) return

      // Verificar el estado REAL del socket en lugar del state de Pinia (que puede estar stale)
      const sock = this._socket
      if (sock) {
        if (sock.readyState === WebSocket.OPEN) {
          console.log('[support] ws already OPEN — skipping connect')
          return
        }
        if (sock.readyState === WebSocket.CONNECTING) {
          console.log('[support] ws already CONNECTING — skipping connect')
          return
        }
        // Socket cerrado o cerrándose — limpiar antes de crear uno nuevo
        try { sock.close() }
        catch { /* ignore */ }
        this._socket = null
      }

      const auth = useAuthStore()
      if (!auth.access) {
        console.warn('[support] no auth token — cannot connect ws')
        return
      }

      const config = useRuntimeConfig()
      const apiBase = (config.public.apiBase as string).replace(/\/rest\/v1\/?$/, '')
      const wsBase = apiBase.replace(/^http/, 'ws')
      const url = `${wsBase}/ws/support/agent/?tenant=${encodeURIComponent(tenantSlug)}&token=${encodeURIComponent(auth.access)}`

      console.log('[support] connecting to', url.replace(/token=[^&]+/, 'token=***'))
      this.wsStatus = 'connecting'
      const ws = new WebSocket(url)
      this._socket = ws

      ws.onopen = () => {
        console.log('[support] ws connected ✓')
        this.wsStatus = 'connected'
      }
      ws.onclose = (ev) => {
        console.warn('[support] ws closed code=', ev.code, 'reason=', ev.reason)
        this.wsStatus = 'disconnected'
        this._socket = null
      }
      ws.onerror = (ev) => {
        console.error('[support] ws error', ev)
        this.wsStatus = 'disconnected'
      }

      ws.onmessage = (ev) => {
        let data: WSEvent
        try { data = JSON.parse(ev.data) }
        catch { return }
        this._handleWSEvent(data)
      }
    },

    sendMessage(text: string) {
      if (!this._socket || this.wsStatus !== 'connected' || !this.activeId) return false
      this._socket.send(JSON.stringify({ type: 'message', content: text }))
      // Optimistic — agregamos localmente para feedback inmediato
      this.messages.push({
        id: `pending-${Date.now()}`,
        sender: 'agent',
        content: text,
        ts: new Date().toISOString()
      })
      return true
    },

    closeActiveConversation() {
      if (!this._socket || this.wsStatus !== 'connected' || !this.activeId) return
      this._socket.send(JSON.stringify({ type: 'close' }))
    },

    _handleWSEvent(data: WSEvent) {
      if (data.type === 'inbox' && data.event === 'new_conversation') {
        // Nueva conversación en la bandeja — refrescar lista
        this.fetchConversations()
        return
      }
      if (data.type === 'opened' && data.conversation_id) {
        this.activeId = data.conversation_id
        return
      }
      if (data.type === 'message' && data.id && (data.content !== undefined || data.attachment_url)) {
        // Reemplazar el optimistic match si existía
        this.messages = this.messages.filter(m => !m.id.startsWith('pending-') || m.content !== data.content)
        this.messages.push({
          id: data.id,
          sender: data.sender ?? 'system',
          content: data.content ?? '',
          attachment_url: data.attachment_url ?? null,
          ts: data.ts ?? new Date().toISOString()
        })
        return
      }
      if (data.type === 'status' && data.status === 'closed') {
        // Conversación cerrada → refrescar lista. Si fue cerrada por el visitante,
        // mostrar mensaje de sistema en el chat y actualizar el status local de la
        // conversación activa (para que el input se deshabilite y muestre "cerrada").
        if (data.closed_by === 'visitor' && this.activeId) {
          this.messages.push({
            id: `system-${Date.now()}`,
            sender: 'system',
            content: 'El visitante cerró la conversación.',
            ts: new Date().toISOString()
          })
          // Actualizar el status local de la conversación activa
          const active = this.conversations.find(c => c.id === this.activeId)
          if (active) active.status = 'closed'
        }
        this.fetchConversations()
      }
    },

    disconnect() {
      if (this._socket) {
        try { this._socket.close() }
        catch { /* ignore */ }
      }
      this._socket = null
      this.wsStatus = 'idle'
    }
  }
})
