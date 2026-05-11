<script setup lang="ts">
import type { FooterContent } from '@agendamiento/shared'

const model = defineModel<FooterContent>({ required: true })

function addLegalLink() {
  model.value.legalLinks.push({ label: '', href: '#' })
}
function removeLegalLink(i: number) {
  model.value.legalLinks.splice(i, 1)
}
</script>

<template>
  <div class="space-y-6">
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Pie de página</p>
      <UFormField label="Tagline (texto bajo el logo)">
        <UTextarea v-model="model.tagline" :rows="2" autoresize />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título columna 1">
          <UInput v-model="model.clinicaSectionTitle" />
        </UFormField>
        <UFormField label="Título columna 2">
          <UInput v-model="model.legalSectionTitle" />
        </UFormField>
      </div>
      <UFormField label="Texto &quot;Powered by&quot;">
        <UInput v-model="model.poweredBy" />
      </UFormField>
    </div>

    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <div class="flex items-center justify-between">
        <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Enlaces legales</p>
        <UButton size="xs" variant="soft" icon="i-lucide-plus" @click="addLegalLink">Añadir</UButton>
      </div>
      <div class="space-y-2">
        <div
          v-for="(link, i) in model.legalLinks"
          :key="i"
          class="flex gap-2"
        >
          <UInput v-model="link.label" placeholder="Etiqueta" class="flex-1" />
          <UInput v-model="link.href" placeholder="URL o #" class="flex-1 font-mono text-xs" />
          <UButton size="sm" color="error" variant="ghost" icon="i-lucide-trash-2" @click="removeLegalLink(i)" />
        </div>
        <p v-if="model.legalLinks.length === 0" class="text-xs text-slate-400 italic">Sin enlaces. Agrega uno con el botón "Añadir".</p>
      </div>
    </div>
  </div>
</template>
