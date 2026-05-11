<script setup lang="ts">
import type { BookingContent } from '@agendamiento/shared'

const model = defineModel<BookingContent>({ required: true })
</script>

<template>
  <div class="space-y-6">
    <!-- Cabecera y pasos -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Cabecera</p>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título de la página">
          <UInput v-model="model.pageTitle" />
        </UFormField>
        <UFormField label="Subtítulo">
          <UInput v-model="model.pageSubtitle" />
        </UFormField>
      </div>
      <div class="grid grid-cols-3 gap-3">
        <UFormField label="Paso 1">
          <UInput v-model="model.stepLabels[0]" />
        </UFormField>
        <UFormField label="Paso 2">
          <UInput v-model="model.stepLabels[1]" />
        </UFormField>
        <UFormField label="Paso 3">
          <UInput v-model="model.stepLabels[2]" />
        </UFormField>
      </div>
    </div>

    <!-- Paso 1 -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Paso 1 — Selección</p>
      <UFormField label="Título &quot;Selecciona el doctor&quot;">
        <UInput v-model="model.step1.doctorTitle" />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título sección motivo">
          <UInput v-model="model.step1.reasonTitle" />
        </UFormField>
        <UFormField label="Etiqueta &quot;(opcional)&quot;">
          <UInput v-model="model.step1.reasonOptionalLabel" />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Placeholder del motivo">
          <UInput v-model="model.step1.reasonPlaceholder" />
        </UFormField>
        <UFormField label="Botón &quot;Sugerir&quot;">
          <UInput v-model="model.step1.reasonButton" />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título &quot;Selecciona el servicio&quot;">
          <UInput v-model="model.step1.serviceTitle" />
        </UFormField>
        <UFormField label="Badge &quot;Sugerido&quot;">
          <UInput v-model="model.step1.suggestedBadge" />
        </UFormField>
      </div>
      <UFormField label="Título &quot;Selecciona la fecha&quot;">
        <UInput v-model="model.step1.dateTitle" />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título &quot;Horario disponible&quot;">
          <UInput v-model="model.step1.slotsTitle" />
        </UFormField>
        <UFormField label="Texto sin disponibilidad">
          <UInput v-model="model.step1.slotsEmpty" />
        </UFormField>
      </div>
      <UFormField label="Botón &quot;Continuar&quot;">
        <UInput v-model="model.step1.continueButton" />
      </UFormField>
    </div>

    <!-- Paso 2 -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Paso 2 — Datos del paciente</p>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Título resumen">
          <UInput v-model="model.step2.summaryTitle" />
        </UFormField>
        <UFormField label="Título del formulario">
          <UInput v-model="model.step2.formTitle" />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Etiqueta nombre">
          <UInput v-model="model.step2.nameLabel" />
        </UFormField>
        <UFormField label="Placeholder nombre">
          <UInput v-model="model.step2.namePlaceholder" />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Etiqueta correo">
          <UInput v-model="model.step2.emailLabel" />
        </UFormField>
        <UFormField label="Placeholder correo">
          <UInput v-model="model.step2.emailPlaceholder" />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Etiqueta teléfono">
          <UInput v-model="model.step2.phoneLabel" />
        </UFormField>
        <UFormField label="Placeholder teléfono">
          <UInput v-model="model.step2.phonePlaceholder" />
        </UFormField>
      </div>
      <UFormField label="Texto privacidad — antes del link">
        <UInput v-model="model.step2.privacyText" />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Texto del link">
          <UInput v-model="model.step2.privacyLinkLabel" />
        </UFormField>
        <UFormField label="Texto privacidad — después del link">
          <UInput v-model="model.step2.privacyTextSuffix" />
        </UFormField>
      </div>
      <div class="grid grid-cols-3 gap-3">
        <UFormField label="Botón Atrás">
          <UInput v-model="model.step2.backButton" />
        </UFormField>
        <UFormField label="Botón Confirmar">
          <UInput v-model="model.step2.confirmButton" />
        </UFormField>
        <UFormField label="Botón mientras envía">
          <UInput v-model="model.step2.confirmingButton" />
        </UFormField>
      </div>
    </div>

    <!-- Paso 3 -->
    <div class="border border-slate-200 rounded-xl p-4 space-y-3">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Paso 3 — Confirmación</p>
      <UFormField label="Título de éxito">
        <UInput v-model="model.step3.successTitle" />
      </UFormField>
      <UFormField label="Mensaje (antes del email)">
        <UInput v-model="model.step3.successMessagePrefix" />
      </UFormField>
      <UFormField label="Botón &quot;Agendar otra cita&quot;">
        <UInput v-model="model.step3.bookAnotherButton" />
      </UFormField>
    </div>
  </div>
</template>
