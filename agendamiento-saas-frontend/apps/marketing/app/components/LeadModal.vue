<script setup>
import { reactive, ref, watch } from 'vue'

const { isOpen, selectedPlan, close } = useLeadModal()
const config = useRuntimeConfig()

const PLAN_LABELS = {
  gratuito: 'Gratuito',
  profesional: 'Profesional',
  clinica: 'Clínica',
  enterprise: 'Enterprise'
}

const form = reactive({ name: '', email: '', phone: '', message: '' })
const status = ref('idle') // idle | sending | success | error
const errorMsg = ref('')

// Reset when the modal opens.
watch(isOpen, (open) => {
  if (open) {
    form.name = ''
    form.email = ''
    form.phone = ''
    form.message = ''
    status.value = 'idle'
    errorMsg.value = ''
  }
})

const planLabel = computed(() => PLAN_LABELS[selectedPlan.value] || '')

async function submit() {
  if (status.value === 'sending') return
  if (!form.name.trim() || !form.email.trim()) {
    errorMsg.value = 'Ingresa tu nombre y correo.'
    status.value = 'error'
    return
  }

  status.value = 'sending'
  errorMsg.value = ''
  try {
    await $fetch(`${config.public.apiBase}/public/leads/`, {
      method: 'POST',
      body: {
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        plan: selectedPlan.value,
        message: form.message.trim(),
        source: 'precios'
      }
    })
    status.value = 'success'
  } catch (e) {
    status.value = 'error'
    errorMsg.value = e?.data?.detail
      || 'No pudimos enviar tu solicitud. Intenta de nuevo en un momento.'
  }
}
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :title="status === 'success' ? 'Solicitud enviada' : 'Solicita información'"
    :description="status === 'success'
      ? undefined
      : planLabel ? `Plan ${planLabel} — te contactamos sin compromiso.` : 'Te contactamos sin compromiso.'"
  >
    <template #body>
      <!-- Success state -->
      <div v-if="status === 'success'" class="py-2">
        <!-- Brand mark: envelope confirmation, navy tile with a soft violet halo -->
        <div class="relative mx-auto mb-5 size-14">
          <span class="absolute -inset-1 rounded-2xl bg-[var(--color-violet-400)]/20 blur-lg" />
          <span class="relative flex size-14 items-center justify-center rounded-2xl bg-primary text-inverted">
            <UIcon name="i-lucide-mail-check" class="size-7" />
          </span>
        </div>

        <p class="text-center text-base leading-relaxed text-highlighted">
          Tu solicitud{{ planLabel ? ` del plan ${planLabel}` : '' }} ya está con nuestro equipo.
          Te escribiremos en menos de un día hábil.
        </p>

        <!-- Confirmation detail -->
        <div class="mt-5 flex items-center gap-3 rounded-xl bg-elevated/60 px-4 py-3">
          <UIcon name="i-lucide-inbox" class="size-5 shrink-0 text-primary" />
          <p class="text-xs leading-relaxed text-muted">
            Revisa tu correo: enviamos una confirmación a
            <span class="font-medium text-default">{{ form.email }}</span>.
          </p>
        </div>

        <UButton
          class="mt-6 justify-center"
          block
          size="lg"
          label="Listo"
          @click="close"
        />
      </div>

      <!-- Form state -->
      <form v-else class="space-y-4" @submit.prevent="submit">
        <UFormField label="Nombre" required>
          <UInput v-model="form.name" placeholder="Dra. Ana Ruiz" autofocus class="w-full" />
        </UFormField>
        <UFormField label="Correo" required>
          <UInput v-model="form.email" type="email" placeholder="ana@consultorio.com" class="w-full" />
        </UFormField>
        <UFormField label="Teléfono (opcional)">
          <UInput v-model="form.phone" placeholder="+52 55 1234 5678" class="w-full" />
        </UFormField>
        <UFormField label="¿Algo que debamos saber? (opcional)">
          <UTextarea v-model="form.message" :rows="3" placeholder="Tengo 3 doctores y dos sucursales…" class="w-full" />
        </UFormField>

        <p v-if="status === 'error'" class="text-sm text-error">
          {{ errorMsg }}
        </p>

        <div class="flex justify-end gap-2 pt-1">
          <UButton label="Cancelar" color="neutral" variant="ghost" @click="close" />
          <UButton
            type="submit"
            :label="status === 'sending' ? 'Enviando…' : 'Enviar solicitud'"
            :loading="status === 'sending'"
            trailing-icon="i-lucide-send"
          />
        </div>
      </form>
    </template>
  </UModal>
</template>
