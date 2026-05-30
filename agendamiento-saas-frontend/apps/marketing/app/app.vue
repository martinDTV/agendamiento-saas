<script setup>
const title = 'NexoSoftDev — Agenda médica con recordatorios por WhatsApp'
const description = 'Software de agendamiento para consultorios y clínicas en México. Reduce inasistencias con recordatorios por WhatsApp, agenda en línea con tu propio dominio y una página de reservas para tus pacientes.'

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', type: 'image/png', href: '/favicon-nexo.png' }
  ],
  htmlAttrs: {
    lang: 'es-MX'
  }
})

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
  twitterCard: 'summary_large_image'
})

const navLinks = [
  { label: 'Funciones', to: '#funciones' },
  { label: 'Cómo funciona', to: '#como-funciona' },
  { label: 'Casos', to: '#casos' },
  { label: 'Precios', to: '#precios' }
]

const year = new Date().getFullYear()
</script>

<template>
  <UApp>
    <UHeader>
      <template #left>
        <NuxtLink to="/" aria-label="NexoSoftDev">
          <AppLogo />
        </NuxtLink>
      </template>

      <UNavigationMenu
        :items="navLinks"
        variant="link"
      />

      <template #right>
        <UButton
          label="Iniciar sesión"
          to="https://app.nexosoftdev.com/login"
          color="neutral"
          variant="ghost"
          class="hidden sm:inline-flex"
        />

        <UButton
          label="Prueba gratis"
          to="/probar"
          trailing-icon="i-lucide-arrow-right"
        />
      </template>

      <template #body>
        <UNavigationMenu
          :items="navLinks"
          orientation="vertical"
          class="-mx-2.5"
        />
        <USeparator class="my-4" />
        <UButton
          label="Iniciar sesión"
          to="https://app.nexosoftdev.com/login"
          color="neutral"
          variant="subtle"
          block
          class="mb-2"
        />
        <UButton
          label="Prueba gratis"
          to="/probar"
          block
        />
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>

    <LeadModal />

    <UFooter>
      <template #top>
        <UContainer>
          <div class="grid gap-8 py-8 sm:grid-cols-2 lg:grid-cols-4">
            <div class="space-y-3">
              <AppLogo />
              <p class="text-sm text-muted max-w-xs">
                Agenda médica en línea para consultorios y clínicas en México.
              </p>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-highlighted mb-3">
                Producto
              </h3>
              <ul class="space-y-2 text-sm text-muted">
                <li><NuxtLink to="/funciones" class="hover:text-default">Funciones</NuxtLink></li>
                <li><NuxtLink to="/#precios" class="hover:text-default">Precios</NuxtLink></li>
                <li><NuxtLink to="/#casos" class="hover:text-default">Casos de uso</NuxtLink></li>
              </ul>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-highlighted mb-3">
                Empresa
              </h3>
              <ul class="space-y-2 text-sm text-muted">
                <li><NuxtLink to="/contacto" class="hover:text-default">Contacto</NuxtLink></li>
                <li><NuxtLink to="/aviso-privacidad" class="hover:text-default">Aviso de privacidad</NuxtLink></li>
                <li><NuxtLink to="/terminos" class="hover:text-default">Términos y condiciones</NuxtLink></li>
              </ul>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-highlighted mb-3">
                Contacto
              </h3>
              <ul class="space-y-2 text-sm text-muted">
                <li><a href="mailto:vazquezmartin1240@gmail.com" class="hover:text-default">vazquezmartin1240@gmail.com</a></li>
                <li>México</li>
              </ul>
            </div>
          </div>
        </UContainer>
      </template>

      <template #left>
        <p class="text-sm text-muted">
          © {{ year }} NexoSoftDev. Hecho en México.
        </p>
      </template>
    </UFooter>
  </UApp>
</template>
