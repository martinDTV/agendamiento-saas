<script setup lang="ts">
import type { HomepageContent } from '@agendamiento/shared'
import IconInput from '../IconInput.vue'

const model = defineModel<HomepageContent>({ required: true })

function addTrustBadge() {
  model.value.hero.trustBadges.push({ icon: 'i-lucide-check', text: '' })
}
function removeTrustBadge(i: number) {
  model.value.hero.trustBadges.splice(i, 1)
}
function addStep() {
  if (model.value.howItWorks.steps.length >= 6) return
  model.value.howItWorks.steps.push({ icon: 'i-lucide-check', title: '', desc: '' })
}
function removeStep(i: number) {
  model.value.howItWorks.steps.splice(i, 1)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Hero -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-4">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Sección Hero</p>
      <UFormField label="Badge superior">
        <UInput v-model="model.hero.badge" placeholder="Agenda tu cita en línea, 24/7" />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título — línea 1">
          <UInput v-model="model.hero.titleLine1" />
        </UFormField>
        <UFormField label="Título — línea 2 (acento)">
          <UInput v-model="model.hero.titleLine2" />
        </UFormField>
      </div>
      <UFormField label="Descripción" hint="Usa {clinica} para insertar el nombre del tenant.">
        <UTextarea v-model="model.hero.description" :rows="3" autoresize />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Botón primario">
          <UInput v-model="model.hero.ctaPrimary" />
        </UFormField>
        <UFormField label="Botón secundario">
          <UInput v-model="model.hero.ctaSecondary" />
        </UFormField>
      </div>

      <div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-medium">Trust badges</p>
          <UButton size="xs" variant="soft" icon="i-lucide-plus" @click="addTrustBadge">Añadir</UButton>
        </div>
        <div class="space-y-2">
          <div
            v-for="(badge, i) in model.hero.trustBadges"
            :key="i"
            class="flex gap-2 items-start"
          >
            <IconInput v-model="badge.icon" />
            <UInput v-model="badge.text" placeholder="Texto del badge" class="flex-1" />
            <UButton size="sm" color="error" variant="ghost" icon="i-lucide-trash-2" @click="removeTrustBadge(i)" />
          </div>
        </div>
      </div>
    </div>

    <!-- ¿Cómo funciona? -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-4">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Sección "¿Cómo funciona?"</p>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título">
          <UInput v-model="model.howItWorks.title" />
        </UFormField>
        <UFormField label="Subtítulo">
          <UInput v-model="model.howItWorks.subtitle" />
        </UFormField>
      </div>

      <div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-medium">Pasos</p>
          <UButton size="xs" variant="soft" icon="i-lucide-plus" :disabled="model.howItWorks.steps.length >= 6" @click="addStep">Añadir</UButton>
        </div>
        <div class="space-y-3">
          <div
            v-for="(step, i) in model.howItWorks.steps"
            :key="i"
            class="border border-slate-200 rounded-lg p-3 space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-slate-500">Paso {{ i + 1 }}</span>
              <UButton size="xs" color="error" variant="ghost" icon="i-lucide-trash-2" @click="removeStep(i)" />
            </div>
            <div class="flex gap-2">
              <IconInput v-model="step.icon" />
              <UInput v-model="step.title" placeholder="Título del paso" class="flex-1" />
            </div>
            <UTextarea v-model="step.desc" :rows="2" placeholder="Descripción" autoresize />
          </div>
        </div>
      </div>
    </div>

    <!-- Servicios -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Sección Servicios</p>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título">
          <UInput v-model="model.services.title" />
        </UFormField>
        <UFormField label="Subtítulo">
          <UInput v-model="model.services.subtitle" />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label='Texto "Ver todos"'>
          <UInput v-model="model.services.seeAllLabel" />
        </UFormField>
        <UFormField label="Texto cuando no hay servicios">
          <UInput v-model="model.services.emptyText" />
        </UFormField>
      </div>
    </div>

    <!-- Equipo -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Sección Equipo / Doctores</p>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título">
          <UInput v-model="model.team.title" />
        </UFormField>
        <UFormField label="Subtítulo">
          <UInput v-model="model.team.subtitle" />
        </UFormField>
      </div>
      <UFormField label="Texto del botón &quot;Agendar&quot; en cada doctor">
        <UInput v-model="model.team.bookButtonLabel" />
      </UFormField>
    </div>

    <!-- CTA final -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">CTA final</p>
      <UFormField label="Título">
        <UInput v-model="model.finalCta.title" />
      </UFormField>
      <UFormField label="Descripción">
        <UTextarea v-model="model.finalCta.description" :rows="2" autoresize />
      </UFormField>
      <UFormField label="Texto del botón">
        <UInput v-model="model.finalCta.buttonText" />
      </UFormField>
    </div>
  </div>
</template>
