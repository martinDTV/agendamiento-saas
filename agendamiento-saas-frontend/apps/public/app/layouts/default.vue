<script setup lang="ts">
const tenant = useTenantStore()
const route = useRoute()
const { content } = useContent()

useBranding()

const isBookingPage = computed(() => route.path === '/agendar')
const logoUrl = computed(() => tenant.tenant?.settings?.branding?.logoUrl ?? '')
const whiteLabel = computed(() => tenant.tenant?.plan_flags?.white_label === true)
</script>

<template>
  <UApp>
    <div class="min-h-screen flex flex-col bg-page">
      <!-- Header -->
      <header class="sticky top-0 z-40 bg-white/90 backdrop-blur-sm border-b border-border">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <!-- Logo / Brand -->
          <NuxtLink to="/" class="flex items-center gap-2.5">
            <img
              v-if="logoUrl"
              :src="logoUrl"
              :alt="tenant.tenant?.name ?? ''"
              class="h-8 w-auto max-w-[140px] object-contain"
            >
            <div v-else class="w-8 h-8 rounded-xl flex items-center justify-center bg-sage-500">
              <UIcon name="i-lucide-calendar-heart" class="text-white text-sm" />
            </div>
            <span v-if="!logoUrl" class="font-semibold text-base text-ink">
              {{ tenant.tenant?.name ?? '…' }}
            </span>
          </NuxtLink>

          <!-- Nav -->
          <nav class="hidden md:flex items-center gap-6 text-sm font-medium text-ink-soft">
            <NuxtLink to="/" class="hover:text-sage-500 transition-colors" :class="route.path === '/' ? 'text-sage-500' : ''">
              {{ content.nav.inicio }}
            </NuxtLink>
            <NuxtLink to="/servicios" class="hover:text-sage-500 transition-colors" :class="route.path === '/servicios' ? 'text-sage-500' : ''">
              {{ content.nav.servicios }}
            </NuxtLink>
            <NuxtLink to="/equipo" class="hover:text-sage-500 transition-colors" :class="route.path === '/equipo' ? 'text-sage-500' : ''">
              {{ content.nav.equipo }}
            </NuxtLink>
            <NuxtLink to="/contacto" class="hover:text-sage-500 transition-colors" :class="route.path === '/contacto' ? 'text-sage-500' : ''">
              {{ content.nav.contacto }}
            </NuxtLink>
          </nav>

          <!-- CTA -->
          <NuxtLink
            v-if="!isBookingPage"
            to="/agendar"
            class="hidden md:inline-flex items-center gap-2 text-sm font-medium text-white px-4 py-2 rounded-lg transition-colors bg-sage-500 hover:bg-sage-600"
          >
            <UIcon name="i-lucide-calendar-plus" class="w-4 h-4" />
            {{ content.nav.ctaLabel }}
          </NuxtLink>

          <!-- Mobile menu placeholder -->
          <button class="md:hidden p-2 rounded-lg hover:bg-page-alt transition-colors text-ink-soft">
            <UIcon name="i-lucide-menu" class="w-5 h-5" />
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1">
        <slot />
      </main>

      <!-- Floating chat bubble (visible en todas las páginas públicas) -->
      <ClientOnly>
        <ChatBubble />
      </ClientOnly>

      <!-- Footer -->
      <footer class="border-t mt-16 border-border bg-page-alt">
        <div class="max-w-7xl mx-auto px-6 py-12">
          <div class="flex flex-col md:flex-row items-start justify-between gap-8">
            <div>
              <div class="flex items-center gap-2.5 mb-3">
                <img
                  v-if="logoUrl"
                  :src="logoUrl"
                  :alt="tenant.tenant?.name ?? ''"
                  class="h-7 w-auto max-w-[120px] object-contain"
                >
                <div v-else class="w-7 h-7 rounded-lg flex items-center justify-center bg-sage-500">
                  <UIcon name="i-lucide-calendar-heart" class="text-white text-xs" />
                </div>
                <span v-if="!logoUrl" class="font-semibold text-ink">{{ tenant.tenant?.name }}</span>
              </div>
              <p class="text-sm max-w-xs text-ink-muted">
                {{ content.footer.tagline }}
              </p>
            </div>

            <div class="flex gap-12 text-sm">
              <div>
                <p class="font-semibold mb-3 text-ink">{{ content.footer.clinicaSectionTitle }}</p>
                <ul class="space-y-2 text-ink-soft">
                  <li><NuxtLink to="/servicios" class="hover:text-sage-500 transition-colors">{{ content.nav.servicios }}</NuxtLink></li>
                  <li><NuxtLink to="/equipo" class="hover:text-sage-500 transition-colors">{{ content.nav.equipo }}</NuxtLink></li>
                  <li><NuxtLink to="/contacto" class="hover:text-sage-500 transition-colors">{{ content.nav.contacto }}</NuxtLink></li>
                  <li><NuxtLink to="/agendar" class="hover:text-sage-500 transition-colors">{{ content.nav.ctaLabel }}</NuxtLink></li>
                </ul>
              </div>
              <div>
                <p class="font-semibold mb-3 text-ink">{{ content.footer.legalSectionTitle }}</p>
                <ul class="space-y-2 text-ink-soft">
                  <li v-for="link in content.footer.legalLinks" :key="link.label">
                    <a :href="link.href" class="hover:text-sage-500 transition-colors">{{ link.label }}</a>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="mt-10 pt-6 border-t flex items-center justify-between text-xs border-border text-ink-muted">
            <p>© {{ new Date().getFullYear() }} {{ tenant.tenant?.name }}. Todos los derechos reservados.</p>
            <p v-if="!whiteLabel">{{ content.footer.poweredBy }}</p>
          </div>
        </div>
      </footer>
    </div>
  </UApp>
</template>
