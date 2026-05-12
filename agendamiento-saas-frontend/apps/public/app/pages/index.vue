<script setup lang="ts">
import type { Service, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: 'tenant' })

const tenant = useTenantStore()
const { apiFetch } = useApi()
const { content } = useContent()

const { data: servicesData } = await useAsyncData('home-services-preview', () =>
  apiFetch<PaginatedResponse<Service>>('/public/catalog/services/')
)

const featuredServices = computed(() =>
  (servicesData.value?.results?.filter(s => s.is_active) ?? []).slice(0, 3)
)
</script>

<template>
  <div>
    <!-- ── HERO ── -->
    <section class="relative overflow-hidden pt-20 pb-24 px-6">
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-0 right-0 w-96 h-96 rounded-full opacity-30 blur-3xl bg-sage-100" />
        <div class="absolute bottom-0 left-1/4 w-64 h-64 rounded-full opacity-20 blur-3xl bg-sage-200" />
      </div>

      <div class="max-w-7xl mx-auto relative">
        <div class="max-w-2xl">
          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-6 bg-sage-100 text-sage-600">
            <span class="w-1.5 h-1.5 rounded-full bg-sage-500" />
            {{ content.homepage.hero.badge }}
          </div>

          <h1 class="text-5xl font-bold leading-tight tracking-tight mb-5 text-ink">
            {{ content.homepage.hero.titleLine1 }} <br>
            <span class="text-sage-500">{{ content.homepage.hero.titleLine2 }}</span>
          </h1>

          <p class="text-lg leading-relaxed mb-8 text-ink-soft">
            {{ content.homepage.hero.description.replace('{clinica}', tenant.tenant?.name ?? 'nuestra clínica') }}
          </p>

          <div class="flex flex-wrap gap-3">
            <NuxtLink
              to="/agendar"
              class="inline-flex items-center gap-2 text-white font-medium px-6 py-3 rounded-xl text-sm transition-all shadow-sm bg-sage-500 hover:bg-sage-600"
            >
              <UIcon name="i-lucide-calendar-plus" class="w-4 h-4" />
              {{ content.homepage.hero.ctaPrimary }}
            </NuxtLink>
            <NuxtLink
              to="/servicios"
              class="inline-flex items-center gap-2 font-medium px-6 py-3 rounded-xl text-sm border transition-all text-ink-soft border-border-strong bg-white hover:border-sage-300"
            >
              {{ content.homepage.hero.ctaSecondary }}
              <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
            </NuxtLink>
          </div>

          <!-- Trust badges -->
          <div class="flex flex-wrap items-center gap-6 mt-10 text-sm text-ink-muted">
            <div
              v-for="(badge, i) in content.homepage.hero.trustBadges"
              :key="i"
              class="flex items-center gap-1.5"
            >
              <UIcon :name="badge.icon" class="w-4 h-4 text-sage-500" />
              {{ badge.text }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── CÓMO FUNCIONA ── -->
    <section class="py-20 px-6 bg-page-alt">
      <div class="max-w-7xl mx-auto">
        <div class="text-center mb-14">
          <h2 class="text-3xl font-bold tracking-tight mb-3 text-ink">{{ content.homepage.howItWorks.title }}</h2>
          <p class="text-base text-ink-soft">{{ content.homepage.howItWorks.subtitle }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div
            v-for="(step, i) in content.homepage.howItWorks.steps"
            :key="i"
            class="relative bg-white rounded-2xl p-7 border border-border shadow-sm"
          >
            <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-5 bg-sage-100">
              <UIcon :name="step.icon" class="w-5 h-5 text-sage-500" />
            </div>
            <div class="absolute top-6 right-6 text-3xl font-bold text-border">0{{ i + 1 }}</div>
            <h3 class="font-semibold text-base mb-2 text-ink">{{ step.title }}</h3>
            <p class="text-sm leading-relaxed text-ink-soft">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ── SERVICIOS DESTACADOS (preview) ── -->
    <section v-if="featuredServices.length > 0" class="py-20 px-6">
      <div class="max-w-7xl mx-auto">
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <h2 class="text-3xl font-bold tracking-tight mb-2 text-ink">{{ content.homepage.services.title }}</h2>
            <p class="text-base text-ink-soft">{{ content.homepage.services.subtitle }}</p>
          </div>
          <NuxtLink
            to="/servicios"
            class="inline-flex items-center gap-2 text-sm font-medium transition-colors text-sage-500 hover:text-sage-600"
          >
            {{ content.homepage.services.seeAllLabel }}
            <UIcon name="i-lucide-arrow-right" class="w-4 h-4" />
          </NuxtLink>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <NuxtLink
            v-for="service in featuredServices"
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
            <p v-if="service.description" class="text-sm mb-4 line-clamp-2 text-ink-soft">{{ service.description }}</p>

            <div class="flex items-center justify-between">
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
      </div>
    </section>

    <!-- ── CTA FINAL ── -->
    <section class="py-24 px-6 bg-page-alt">
      <div class="max-w-2xl mx-auto text-center">
        <div class="inline-flex w-14 h-14 rounded-2xl items-center justify-center mb-6 bg-sage-100">
          <UIcon name="i-lucide-calendar-heart" class="w-7 h-7 text-sage-500" />
        </div>
        <h2 class="text-3xl font-bold tracking-tight mb-4 text-ink">
          {{ content.homepage.finalCta.title }}
        </h2>
        <p class="text-base leading-relaxed mb-8 text-ink-soft">
          {{ content.homepage.finalCta.description }}
        </p>
        <NuxtLink
          to="/agendar"
          class="inline-flex items-center gap-2 text-white font-medium px-8 py-3.5 rounded-xl text-sm transition-all shadow-sm bg-sage-500 hover:bg-sage-600"
        >
          <UIcon name="i-lucide-calendar-plus" class="w-4 h-4" />
          {{ content.homepage.finalCta.buttonText }}
        </NuxtLink>
      </div>
    </section>
  </div>
</template>
