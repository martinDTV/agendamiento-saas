<script setup lang="ts">
import type { SiteContent } from '@agendamiento/shared'
import NavForm from './forms/NavForm.vue'
import HomepageForm from './forms/HomepageForm.vue'
import BookingForm from './forms/BookingForm.vue'
import FooterForm from './forms/FooterForm.vue'

const model = defineModel<SiteContent>({ required: true })

const items = [
  { key: 'nav',      label: 'Navegación', icon: 'i-lucide-menu' },
  { key: 'homepage', label: 'Inicio',     icon: 'i-lucide-home' },
  { key: 'booking',  label: 'Reservas',   icon: 'i-lucide-calendar-plus' },
  { key: 'footer',   label: 'Footer',     icon: 'i-lucide-panel-bottom' },
]
const active = ref('nav')
</script>

<template>
  <div class="space-y-4">
    <!-- Tab nav -->
    <div class="flex gap-1 p-1 bg-slate-100 rounded-lg overflow-x-auto">
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all whitespace-nowrap"
        :class="active === item.key
          ? 'bg-white text-slate-900 shadow-sm'
          : 'text-slate-500 hover:text-slate-700'"
        @click="active = item.key"
      >
        <UIcon :name="item.icon" class="w-3.5 h-3.5" />
        {{ item.label }}
      </button>
    </div>

    <!-- Tab content -->
    <div v-show="active === 'nav'">
      <NavForm v-model="model.nav" />
    </div>
    <div v-show="active === 'homepage'">
      <HomepageForm v-model="model.homepage" />
    </div>
    <div v-show="active === 'booking'">
      <BookingForm v-model="model.booking" />
    </div>
    <div v-show="active === 'footer'">
      <FooterForm v-model="model.footer" />
    </div>
  </div>
</template>
