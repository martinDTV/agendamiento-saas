<script setup lang="ts">
import type { Service, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: 'tenant' })

const { apiFetch } = useApi()
const { content } = useContent()

const { data: servicesData } = await useAsyncData('public-services-page', () =>
  apiFetch<PaginatedResponse<Service>>('/public/catalog/services/')
)

const services = computed(() => servicesData.value?.results?.filter(s => s.is_active) ?? [])
</script>

<template>
  <div>
    <!-- ── PAGE HERO ── -->
    <section class="relative overflow-hidden pt-16 pb-12 px-6">
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-0 right-0 w-96 h-96 rounded-full opacity-20 blur-3xl bg-sage-100" />
      </div>
      <div class="max-w-7xl mx-auto relative text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4 bg-sage-100 text-sage-600">
          <UIcon name="i-lucide-stethoscope" class="w-3.5 h-3.5" />
          {{ content.nav.servicios }}
        </div>
        <h1 class="text-4xl font-bold tracking-tight mb-3 text-ink">
          {{ content.homepage.services.title }}
        </h1>
        <p class="text-base text-ink-soft max-w-2xl mx-auto">
          {{ content.homepage.services.subtitle }}
        </p>
      </div>
    </section>

    <!-- ── SERVICES GRID ── -->
    <section class="pb-20 px-6">
      <div class="max-w-7xl mx-auto">
        <div v-if="!servicesData" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div v-for="i in 6" :key="i" class="h-44 rounded-2xl animate-pulse bg-page-alt" />
        </div>

        <div v-else-if="services.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <NuxtLink
            v-for="service in services"
            :key="service.id"
            to="/agendar"
            class="group bg-white rounded-2xl p-6 border border-border shadow-sm transition-all duration-200 hover:shadow-md hover:border-sage-300"
          >
            <div class="flex items-start justify-between mb-4">
              <div
                class="w-10 h-10 rounded-xl flex items-center justify-center"
                :class="!service.color ? 'bg-sage-100' : ''"
                :style="service.color ? { backgroundColor: service.color + '22' } : undefined"
              >
                <span
                  class="w-3 h-3 rounded-full"
                  :class="!service.color ? 'bg-sage-500' : ''"
                  :style="service.color ? { backgroundColor: service.color } : undefined"
                />
              </div>
              <UIcon name="i-lucide-arrow-up-right" class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-sage-500" />
            </div>

            <h3 class="font-semibold text-base mb-1 text-ink">{{ service.name }}</h3>
            <p v-if="service.description" class="text-sm mb-4 line-clamp-3 text-ink-soft">{{ service.description }}</p>

            <div class="flex items-center justify-between pt-3 border-t border-border">
              <div class="flex items-center gap-1.5 text-xs text-ink-muted">
                <UIcon name="i-lucide-clock" class="w-3.5 h-3.5" />
                {{ service.duration }} min
              </div>
              <span class="text-sm font-semibold text-ink">
                ${{ parseFloat(service.price).toFixed(0) }} MXN
              </span>
            </div>
          </NuxtLink>
        </div>

        <div v-else class="text-center py-16 text-ink-muted">
          <UIcon name="i-lucide-clipboard-list" class="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p class="text-sm">{{ content.homepage.services.emptyText }}</p>
        </div>
      </div>
    </section>

    <!-- ── CTA FINAL ── -->
    <section class="py-16 px-6 bg-page-alt">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-2xl font-bold tracking-tight mb-3 text-ink">
          {{ content.homepage.finalCta.title }}
        </h2>
        <p class="text-base text-ink-soft mb-6">
          {{ content.homepage.finalCta.description }}
        </p>
        <NuxtLink
          to="/agendar"
          class="inline-flex items-center gap-2 text-white font-medium px-6 py-3 rounded-xl text-sm transition-all shadow-sm bg-sage-500 hover:bg-sage-600"
        >
          <UIcon name="i-lucide-calendar-plus" class="w-4 h-4" />
          {{ content.homepage.finalCta.buttonText }}
        </NuxtLink>
      </div>
    </section>
  </div>
</template>
