<script setup>
import { reactive, ref } from 'vue'

useSeoMeta({
  title: 'Contacto — NexoSoftDev',
  description: 'Habla con NexoSoftDev. Te respondemos en menos de un día hábil.'
})

const config = useRuntimeConfig()

const form = reactive({ name: '', email: '', phone: '', message: '' })
const status = ref('idle') // idle | sending | success | error
const fieldErrors = reactive({ name: '', email: '' })
const errorMsg = ref('')

function validate() {
  fieldErrors.name = form.name.trim().length < 2 ? 'Ingresa tu nombre.' : ''
  fieldErrors.email = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim()) ? '' : 'Ingresa un correo válido.'
  return !fieldErrors.name && !fieldErrors.email
}

async function submit() {
  if (status.value === 'sending') return
  if (!validate()) {
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
        message: form.message.trim(),
        source: 'contacto'
      }
    })
    status.value = 'success'
  } catch (e) {
    status.value = 'error'
    errorMsg.value = e?.data?.detail || 'No pudimos enviar tu mensaje. Intenta de nuevo en un momento.'
  }
}

const channels = [
  {
    icon: 'i-lucide-mail',
    label: 'Correo',
    value: 'vazquezmartin1240@gmail.com',
    href: 'mailto:vazquezmartin1240@gmail.com'
  },
  {
    icon: 'i-lucide-map-pin',
    label: 'Ubicación',
    value: 'Guadalupe, Nuevo León, México',
    href: null
  },
  {
    icon: 'i-lucide-clock',
    label: 'Respuesta',
    value: 'En menos de un día hábil',
    href: null
  }
]
</script>

<template>
  <UContainer class="py-16 sm:py-24">
    <!-- Split: left = pitch + channels, right = inline form. Asymmetric, left-aligned. -->
    <div class="grid gap-12 lg:grid-cols-[1fr_1.1fr] lg:gap-16">
      <!-- Left column -->
      <div>
        <p class="text-sm font-medium text-primary">
          Contacto
        </p>
        <h1 class="mt-3 text-4xl font-medium tracking-tight text-highlighted sm:text-5xl">
          Pongamos tu agenda<br>a trabajar
        </h1>
        <p class="mt-5 max-w-md text-lg leading-relaxed text-muted">
          Cuéntanos de tu consultorio y te mostramos cómo NexoSoftDev reduce
          inasistencias desde la primera semana.
        </p>

        <!-- Channels, separated by lines instead of boxed cards -->
        <dl class="mt-10 divide-y divide-default border-y border-default">
          <div
            v-for="(c, i) in channels"
            :key="i"
            class="flex items-center gap-4 py-4"
          >
            <span class="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
              <UIcon :name="c.icon" class="size-5 text-primary" />
            </span>
            <div>
              <dt class="text-xs uppercase tracking-wide text-muted">
                {{ c.label }}
              </dt>
              <dd class="mt-0.5 text-sm font-medium text-highlighted">
                <a v-if="c.href" :href="c.href" class="hover:text-primary">{{ c.value }}</a>
                <span v-else>{{ c.value }}</span>
              </dd>
            </div>
          </div>
        </dl>
      </div>

      <!-- Right column: form panel -->
      <div class="rounded-3xl border border-default bg-elevated/30 p-8 sm:p-10">
        <!-- Success -->
        <div v-if="status === 'success'" class="flex h-full flex-col items-start justify-center gap-5 py-6">
          <span class="flex size-14 items-center justify-center rounded-2xl bg-primary text-inverted">
            <UIcon name="i-lucide-mail-check" class="size-7" />
          </span>
          <div>
            <h2 class="text-xl font-medium text-highlighted">
              Mensaje recibido
            </h2>
            <p class="mt-2 max-w-sm text-muted">
              Te enviamos una confirmación a tu correo. Te escribimos en menos de
              un día hábil.
            </p>
          </div>
        </div>

        <!-- Form -->
        <form v-else class="space-y-5" novalidate @submit.prevent="submit">
          <div class="space-y-2">
            <label for="c-name" class="block text-sm font-medium text-highlighted">Nombre</label>
            <UInput
              id="c-name"
              v-model="form.name"
              placeholder="Dra. Mariana Esquivel"
              size="lg"
              class="w-full"
              :color="fieldErrors.name ? 'error' : undefined"
            />
            <p v-if="fieldErrors.name" class="text-sm text-error">{{ fieldErrors.name }}</p>
          </div>

          <div class="space-y-2">
            <label for="c-email" class="block text-sm font-medium text-highlighted">Correo</label>
            <UInput
              id="c-email"
              v-model="form.email"
              type="email"
              placeholder="mariana@consultorio.com"
              size="lg"
              class="w-full"
              :color="fieldErrors.email ? 'error' : undefined"
            />
            <p v-if="fieldErrors.email" class="text-sm text-error">{{ fieldErrors.email }}</p>
          </div>

          <div class="space-y-2">
            <label for="c-phone" class="block text-sm font-medium text-highlighted">
              Teléfono <span class="font-normal text-muted">(opcional)</span>
            </label>
            <UInput id="c-phone" v-model="form.phone" placeholder="+52 81 1234 5678" size="lg" class="w-full" />
          </div>

          <div class="space-y-2">
            <label for="c-msg" class="block text-sm font-medium text-highlighted">
              Mensaje <span class="font-normal text-muted">(opcional)</span>
            </label>
            <UTextarea id="c-msg" v-model="form.message" :rows="4" placeholder="Tengo 3 doctores en dos sucursales y pierdo citas por inasistencias." class="w-full" />
          </div>

          <p v-if="status === 'error' && errorMsg" class="text-sm text-error">
            {{ errorMsg }}
          </p>

          <UButton
            type="submit"
            block
            size="lg"
            class="justify-center active:scale-[0.98]"
            :loading="status === 'sending'"
            :label="status === 'sending' ? 'Enviando…' : 'Enviar mensaje'"
            trailing-icon="i-lucide-arrow-right"
          />
          <p class="text-center text-xs text-muted">
            Al enviar, aceptas nuestro
            <NuxtLink to="/aviso-privacidad" class="underline hover:text-default">aviso de privacidad</NuxtLink>.
          </p>
        </form>
      </div>
    </div>
  </UContainer>
</template>
