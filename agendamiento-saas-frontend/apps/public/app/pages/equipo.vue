<script setup lang="ts">
import type { Doctor, PaginatedResponse } from '@agendamiento/shared'

definePageMeta({ middleware: 'tenant' })

const { apiFetch } = useApi()
const { content } = useContent()

const { data: doctorsData } = await useAsyncData('public-doctors-page', () =>
  apiFetch<PaginatedResponse<Doctor>>('/public/catalog/doctors/')
)

const doctors = computed(() => doctorsData.value?.results?.filter(d => d.is_active) ?? [])
</script>

<template>
  <div>
    <!-- ── PAGE HERO ── -->
    <section class="relative overflow-hidden pt-16 pb-12 px-6">
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-0 left-0 w-96 h-96 rounded-full opacity-20 blur-3xl bg-sage-100" />
      </div>
      <div class="max-w-7xl mx-auto relative text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4 bg-sage-100 text-sage-600">
          <UIcon name="i-lucide-users" class="w-3.5 h-3.5" />
          {{ content.nav.equipo }}
        </div>
        <h1 class="text-4xl font-bold tracking-tight mb-3 text-ink">
          {{ content.homepage.team.title }}
        </h1>
        <p class="text-base text-ink-soft max-w-2xl mx-auto">
          {{ content.homepage.team.subtitle }}
        </p>
      </div>
    </section>

    <!-- ── TEAM GRID ── -->
    <section class="pb-20 px-6">
      <div class="max-w-7xl mx-auto">
        <div v-if="!doctorsData" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div v-for="i in 6" :key="i" class="h-56 rounded-2xl animate-pulse bg-page-alt" />
        </div>

        <div v-else-if="doctors.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="doctor in doctors"
            :key="doctor.id"
            class="bg-white rounded-2xl p-6 border border-border shadow-sm text-center transition-all hover:shadow-md"
          >
            <div class="w-20 h-20 rounded-full overflow-hidden mx-auto mb-4 flex items-center justify-center text-2xl font-bold bg-sage-100 text-sage-500 ring-2 ring-white shadow-sm">
              <img v-if="doctor.photo" :src="doctor.photo" :alt="doctor.full_name" class="w-full h-full object-cover">
              <template v-else>{{ doctor.full_name?.[0]?.toUpperCase() }}</template>
            </div>
            <h3 class="font-semibold text-base text-ink">{{ doctor.full_name }}</h3>
            <p class="text-sm mt-1 mb-4 text-ink-soft">{{ doctor.specialty || 'Médico General' }}</p>
            <NuxtLink
              to="/agendar"
              class="inline-flex items-center gap-1.5 text-xs font-medium px-4 py-2 rounded-lg transition-colors bg-sage-100 text-sage-600 hover:bg-sage-200"
            >
              <UIcon name="i-lucide-calendar-plus" class="w-3.5 h-3.5" />
              {{ content.homepage.team.bookButtonLabel }}
            </NuxtLink>
          </div>
        </div>

        <div v-else class="text-center py-16 text-ink-muted">
          <UIcon name="i-lucide-user-x" class="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p class="text-sm">No hay miembros del equipo disponibles.</p>
        </div>
      </div>
    </section>
  </div>
</template>
