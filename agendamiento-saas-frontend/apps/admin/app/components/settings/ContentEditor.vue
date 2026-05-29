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
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 ease-out whitespace-nowrap"
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
    <Transition name="tab-fade" mode="out-in">
      <NavForm v-if="active === 'nav'" key="nav" v-model="model.nav" />
      <HomepageForm v-else-if="active === 'homepage'" key="homepage" v-model="model.homepage" />
      <BookingForm v-else-if="active === 'booking'" key="booking" v-model="model.booking" />
      <FooterForm v-else-if="active === 'footer'" key="footer" v-model="model.footer" />
    </Transition>
  </div>
</template>

<style scoped>
/* Fade corto al cambiar de pestaña — ease-out porque es una entrada. */
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 150ms cubic-bezier(0.23, 1, 0.32, 1);
}
.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .tab-fade-enter-active,
  .tab-fade-leave-active {
    transition: none;
  }
}
</style>
