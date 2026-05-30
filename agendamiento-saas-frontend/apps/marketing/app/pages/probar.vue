<script setup>
import { computed, ref } from 'vue'

useSeoMeta({
  title: 'Prueba la demo — NexoSoftDev',
  description: 'Crea tu clínica de demostración en segundos y explora el panel y el sitio de reservas con datos de ejemplo.'
})

const DEMO_DOMAIN = 'demo-agendamiento.nexosoftdev.com'

const name = ref('')

// Convert a clinic name to a URL-safe slug.
const slug = computed(() => {
  return name.value
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // strip accents
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 40)
    .replace(/^-|-$/g, '')
})

const ready = computed(() => slug.value.length >= 2)
const patientUrl = computed(() => `https://${slug.value}.${DEMO_DOMAIN}`)
const panelUrl = computed(() => `https://${slug.value}.${DEMO_DOMAIN}/panel`)
const adminEmail = computed(() => `admin@${slug.value}.demo.local`)

const created = ref(false)
function go() {
  if (!ready.value) return
  created.value = true
}
</script>

<template>
  <UContainer class="py-16 sm:py-24">
    <div class="mx-auto max-w-xl">
      <p class="text-sm font-medium text-primary">
        Demo en vivo
      </p>
      <h1 class="mt-3 text-4xl font-medium tracking-tight text-highlighted sm:text-5xl">
        Crea tu clínica de prueba
      </h1>
      <p class="mt-5 text-lg leading-relaxed text-muted">
        Escribe el nombre de tu consultorio. Generamos una demo con datos de
        ejemplo (doctores, servicios y citas) en segundos. Sin tarjeta, sin
        instalar nada.
      </p>

      <!-- Step 1: choose name -->
      <div v-if="!created" class="mt-10 space-y-4">
        <div class="space-y-2">
          <label for="clinic" class="block text-sm font-medium text-highlighted">
            Nombre de tu consultorio o clínica
          </label>
          <UInput
            id="clinic"
            v-model="name"
            placeholder="Clínica del Valle"
            size="xl"
            class="w-full"
            autofocus
            @keyup.enter="go"
          />
          <p v-if="slug" class="text-sm text-muted">
            Tu demo:
            <span class="font-medium text-default">{{ slug }}.{{ DEMO_DOMAIN }}</span>
          </p>
        </div>

        <UButton
          size="xl"
          block
          class="justify-center"
          :disabled="!ready"
          trailing-icon="i-lucide-arrow-right"
          label="Crear mi demo"
          @click="go"
        />
        <p class="text-center text-xs text-muted">
          La demo se borra automáticamente a los 7 días.
        </p>
      </div>

      <!-- Step 2: ready, show links + credentials -->
      <div v-else class="mt-10 space-y-6">
        <div class="flex items-center gap-3 rounded-xl bg-primary/10 p-4">
          <UIcon name="i-lucide-check-circle-2" class="size-6 shrink-0 text-primary" />
          <p class="text-sm text-default">
            Tu demo <span class="font-medium text-highlighted">{{ slug }}</span> está lista.
            La clínica se crea al abrir el primer enlace.
          </p>
        </div>

        <!-- Patient site -->
        <div class="rounded-2xl border border-default p-6">
          <h2 class="font-medium text-highlighted">
            Sitio de reservas (lo que ven tus pacientes)
          </h2>
          <p class="mt-1 text-sm text-muted">
            La página donde tus pacientes agendan en línea.
          </p>
          <UButton
            class="mt-4"
            :to="patientUrl"
            target="_blank"
            trailing-icon="i-lucide-external-link"
            label="Abrir sitio de reservas"
          />
        </div>

        <!-- Admin panel -->
        <div class="rounded-2xl border border-default p-6">
          <h2 class="font-medium text-highlighted">
            Panel de administración (para ti y tu equipo)
          </h2>
          <p class="mt-1 text-sm text-muted">
            Agenda, doctores, servicios y reportes. Entra con estas credenciales de demo:
          </p>
          <dl class="mt-4 space-y-2 rounded-xl bg-elevated/60 p-4 text-sm">
            <div class="flex justify-between gap-3">
              <dt class="text-muted">Correo</dt>
              <dd class="font-medium text-default break-all">{{ adminEmail }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt class="text-muted">Contraseña</dt>
              <dd class="font-medium text-default">Demo2024!</dd>
            </div>
          </dl>
          <UButton
            class="mt-4"
            :to="panelUrl"
            target="_blank"
            color="neutral"
            variant="subtle"
            trailing-icon="i-lucide-external-link"
            label="Abrir panel de administración"
          />
        </div>

        <button
          type="button"
          class="text-sm text-muted underline hover:text-default"
          @click="created = false"
        >
          Crear otra demo
        </button>
      </div>
    </div>
  </UContainer>
</template>
