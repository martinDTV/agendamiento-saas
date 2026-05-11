<script setup lang="ts">
import type { NavContent } from '@agendamiento/shared'

const model = defineModel<NavContent>({ required: true })
</script>

<template>
  <div class="space-y-4">
    <p class="text-sm text-slate-500">Etiquetas del menú superior y CTA principal del sitio público.</p>
    <div class="grid grid-cols-2 gap-3">
      <UFormField label="Inicio">
        <UInput v-model="model.inicio" />
      </UFormField>
      <UFormField label="Servicios">
        <UInput v-model="model.servicios" />
      </UFormField>
      <UFormField label="Equipo">
        <UInput v-model="model.equipo" />
      </UFormField>
      <UFormField label="Contacto">
        <UInput v-model="model.contacto" />
      </UFormField>
    </div>
    <UFormField label="CTA del header (botón &quot;Agendar cita&quot;)">
      <UInput v-model="model.ctaLabel" />
    </UFormField>
  </div>
</template>
