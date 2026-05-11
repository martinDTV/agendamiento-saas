<script setup lang="ts">
import type { Membership, MembershipRole } from '@agendamiento/shared'

definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })

const { apiFetch } = useApi()
const toast = useToast()

interface InvitationToken {
  id: string
  email: string
  role: MembershipRole
  created_at: string
}

const members = ref<Membership[]>([])
const invitations = ref<InvitationToken[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [mem, inv] = await Promise.all([
      apiFetch<Membership[]>('/accounts/memberships/'),
      apiFetch<InvitationToken[]>('/accounts/invitations/')
    ])
    members.value = Array.isArray(mem) ? mem : (mem as any).results ?? []
    invitations.value = Array.isArray(inv) ? inv : (inv as any).results ?? []
  }
  finally { loading.value = false }
}

async function changeRole(m: Membership, role: string) {
  await apiFetch(`/accounts/memberships/${m.id}/`, { method: 'PATCH', body: { role } })
  toast.add({ title: 'Rol actualizado', color: 'primary' })
  load()
}

async function deactivate(m: Membership) {
  await apiFetch(`/accounts/memberships/${m.id}/`, { method: 'PATCH', body: { is_active: false } })
  toast.add({ title: 'Miembro desactivado', color: 'primary' })
  load()
}

// ── Cancel invitation confirmation modal ─────────────────────────────────────
const cancelTarget = ref<InvitationToken | null>(null)
const cancelling = ref(false)

function askCancelInvitation(inv: InvitationToken) {
  cancelTarget.value = inv
}

async function confirmCancelInvitation() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try {
    await apiFetch(`/accounts/invitations/${cancelTarget.value.id}/`, { method: 'DELETE' })
    toast.add({ title: 'Invitación cancelada', color: 'primary' })
    cancelTarget.value = null
    load()
  }
  catch (err: any) {
    const msg = err?.response?.data?.detail ?? 'No se pudo cancelar la invitación'
    toast.add({ title: msg, color: 'error' })
  }
  finally {
    cancelling.value = false
  }
}

// ── Invite form ───────────────────────────────────────────────────────────────
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteRole = ref<string>('staff')
const inviting = ref(false)

const roleOptions = [
  { label: 'Admin', value: 'admin' },
  { label: 'Doctor', value: 'doctor' },
  { label: 'Soporte', value: 'support' },
  { label: 'Staff', value: 'staff' }
]

const roleLabels: Record<string, string> = {
  owner: 'Propietario',
  admin: 'Administrador',
  support: 'Soporte',
  doctor: 'Doctor',
  staff: 'Staff'
}

const roleBadgeColor: Record<string, string> = {
  owner: 'purple',
  admin: 'blue',
  doctor: 'green',
  support: 'orange',
  staff: 'neutral'
}

async function sendInvite() {
  if (!inviteEmail.value) return
  inviting.value = true
  try {
    await apiFetch('/accounts/invitations/', {
      method: 'POST',
      body: { email: inviteEmail.value, role: inviteRole.value }
    })
    toast.add({ title: `Invitación enviada a ${inviteEmail.value}`, color: 'primary' })
    inviteEmail.value = ''
    inviteRole.value = 'staff'
    showInvite.value = false
    load()
  }
  catch (err: any) {
    const msg = err?.response?.data?.email?.[0] ?? 'Error al enviar la invitación'
    toast.add({ title: msg, color: 'error' })
  }
  finally { inviting.value = false }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Equipo</h1>
        <p class="text-sm text-slate-400 mt-0.5">
          Invitá usuarios por correo con cualquier rol (admin, doctor, soporte, staff).
          Para crear un doctor con todos los datos cargados de una vez (especialidad, sucursal, foto), también podés usar
          <NuxtLink to="/doctors" class="text-sage-600 font-medium hover:underline">Doctores</NuxtLink>.
        </p>
      </div>
      <UButton icon="i-lucide-user-plus" @click="showInvite = true">Invitar miembro</UButton>
    </div>

    <!-- Invite modal -->
    <UModal v-model:open="showInvite" title="Invitar nuevo miembro">
      <template #content>
        <form class="space-y-4 p-6" @submit.prevent="sendInvite">
          <h3 class="text-base font-semibold text-slate-800">Invitar nuevo miembro</h3>
          <p class="text-xs text-slate-500 -mt-2">
            Se enviará un email con un link de invitación. El usuario aceptará y se creará la cuenta.
          </p>

          <UFormField label="Email">
            <UInput v-model="inviteEmail" type="email" placeholder="usuario@ejemplo.com" autofocus class="w-full" />
          </UFormField>

          <UFormField label="Rol" hint="Soporte: atiende el chat público | Staff: acceso básico al panel">
            <USelect
              v-model="inviteRole"
              :items="roleOptions"
              value-attribute="value"
              label-attribute="label"
              class="w-full"
            />
          </UFormField>

          <div class="flex justify-end gap-2 pt-2 border-t" style="border-color: #F3F4F6;">
            <UButton variant="ghost" color="neutral" @click="showInvite = false">Cancelar</UButton>
            <UButton type="submit" :loading="inviting" :disabled="!inviteEmail">
              Enviar invitación
            </UButton>
          </div>
        </form>
      </template>
    </UModal>

    <!-- Members table -->
    <UCard :ui="{ body: 'p-0' }">
      <template #header>
        <p class="font-semibold px-1">Miembros activos</p>
      </template>
      <div v-if="loading" class="flex justify-center py-10">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-sage-500" />
      </div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-800/50">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Email</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Rol</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
          <tr v-for="m in members" :key="m.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
            <td class="px-4 py-3">{{ m.user_email }}</td>
            <td class="px-4 py-3">
              <UBadge :color="roleBadgeColor[m.role] ?? 'neutral'" variant="soft">
                {{ roleLabels[m.role] ?? m.role }}
              </UBadge>
            </td>
            <td class="px-4 py-3">
              <UBadge :color="m.is_active ? 'green' : 'neutral'" variant="soft">
                {{ m.is_active ? 'Activo' : 'Inactivo' }}
              </UBadge>
            </td>
            <td class="px-4 py-3">
              <div v-if="m.role !== 'owner'" class="flex gap-1 justify-end">
                <UDropdownMenu
                  :items="roleOptions
                    .filter(r => r.value !== m.role)
                    .map(r => ({ label: `Cambiar a ${r.label}`, onSelect: () => changeRole(m, r.value) }))"
                >
                  <UButton size="xs" variant="ghost" icon="i-lucide-user-cog" />
                </UDropdownMenu>
                <UButton
                  v-if="m.is_active"
                  size="xs"
                  variant="ghost"
                  color="error"
                  icon="i-lucide-user-minus"
                  @click="deactivate(m)"
                />
              </div>
            </td>
          </tr>
          <tr v-if="members.length === 0">
            <td colspan="4" class="text-center py-10 text-gray-400">Sin miembros</td>
          </tr>
        </tbody>
      </table>
    </UCard>

    <!-- Cancel invitation confirmation modal -->
    <UModal :open="!!cancelTarget" title="Cancelar invitación" @update:open="(v) => { if (!v) cancelTarget = null }">
      <template #content>
        <div class="p-6 space-y-4">
          <div class="flex items-start gap-3 p-4 rounded-xl bg-rose-50 border border-rose-200">
            <UIcon name="i-lucide-triangle-alert" class="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div class="text-sm text-rose-900">
              <p class="font-semibold">¿Cancelar la invitación?</p>
              <p class="mt-1 text-rose-800">
                El enlace enviado a <strong>{{ cancelTarget?.email }}</strong> dejará de funcionar
                inmediatamente. Si esa persona aún quiere unirse, vas a tener que enviar otra invitación.
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2 border-t" style="border-color: #F3F4F6;">
            <UButton variant="ghost" color="neutral" @click="cancelTarget = null">
              Volver
            </UButton>
            <UButton
              color="error"
              :loading="cancelling"
              icon="i-lucide-trash-2"
              @click="confirmCancelInvitation"
            >
              Sí, cancelar
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Pending invitations -->
    <UCard v-if="invitations.length > 0" :ui="{ body: 'p-0' }">
      <template #header>
        <p class="font-semibold px-1">Invitaciones pendientes</p>
      </template>
      <table class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-800/50">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Email</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Rol</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Enviada</th>
            <th class="px-4 py-3" />
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
          <tr v-for="inv in invitations" :key="inv.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
            <td class="px-4 py-3">{{ inv.email }}</td>
            <td class="px-4 py-3">
              <UBadge :color="roleBadgeColor[inv.role] ?? 'neutral'" variant="soft">
                {{ roleLabels[inv.role] ?? inv.role }}
              </UBadge>
            </td>
            <td class="px-4 py-3 text-gray-400">
              {{ new Date(inv.created_at).toLocaleDateString('es-MX') }}
            </td>
            <td class="px-4 py-3 text-right">
              <UButton
                size="xs"
                variant="ghost"
                color="error"
                icon="i-lucide-trash-2"
                @click="askCancelInvitation(inv)"
              >
                Cancelar
              </UButton>
            </td>
          </tr>
        </tbody>
      </table>
    </UCard>
  </div>
</template>
