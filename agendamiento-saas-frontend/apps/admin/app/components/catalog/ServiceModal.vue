<script setup lang="ts">
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import type { Service, Doctor, PaginatedResponse } from '@agendamiento/shared'

const props = defineProps<{ service: Service | null }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>('open')

const { apiFetch } = useApi()
const toast = useToast()

const schema = toTypedSchema(z.object({
  name: z.string().min(1, 'Requerido'),
  description: z.string().optional().default(''),
  duration: z.coerce.number().min(5, 'Mínimo 5 min'),
  price: z.coerce.number().min(0),
  color: z.string().default('#3B82F6'),
  doctor_ids: z.array(z.string()).default([])
}))

const { handleSubmit, errors, defineField, resetForm } = useForm({ validationSchema: schema })
const [name, nameA] = defineField('name')
const [description, descA] = defineField('description')
const [duration, durA] = defineField('duration')
const [price, priceA] = defineField('price')
const [color, colorA] = defineField('color')
const [doctorIds] = defineField('doctor_ids')

const doctors = ref<Doctor[]>([])
const loadingDoctors = ref(false)

async function loadDoctors() {
  loadingDoctors.value = true
  try {
    const res = await apiFetch<PaginatedResponse<Doctor>>('/catalog/doctors/')
    doctors.value = res.results.filter(d => d.is_active)
  }
  finally { loadingDoctors.value = false }
}

watch(open, val => {
  if (val) {
    resetForm({ values: {
      name: props.service?.name ?? '',
      description: props.service?.description ?? '',
      duration: props.service?.duration ?? 30,
      price: props.service?.price ? parseFloat(props.service.price) : 0,
      color: props.service?.color ?? '#3B82F6',
      doctor_ids: props.service?.doctor_ids ?? []
    } })
    if (doctors.value.length === 0) loadDoctors()
  }
})

function toggleDoctor(id: string) {
  const current = doctorIds.value ?? []
  doctorIds.value = current.includes(id)
    ? current.filter((x: string) => x !== id)
    : [...current, id]
}

const loading = ref(false)
const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    props.service
      ? await apiFetch(`/catalog/services/${props.service.id}/`, { method: 'PATCH', body: values })
      : await apiFetch('/catalog/services/', { method: 'POST', body: values })
    toast.add({ title: 'Guardado', color: 'primary' })
    open.value = false
    emit('saved')
  }
  catch (err: any) {
    const data = err?.response?.data ?? err?.data ?? {}
    const msg = data.detail ?? Object.values(data).flat().join(' · ') ?? 'Error al guardar'
    toast.add({ title: msg, color: 'error' })
  }
  finally { loading.value = false }
})
</script>

<template>
  <UModal v-model:open="open" :title="service ? 'Editar servicio' : 'Nuevo servicio'">
    <template #content>
      <form class="space-y-4 p-6" @submit.prevent="onSubmit">
        <h3 class="text-base font-semibold text-slate-800">{{ service ? 'Editar servicio' : 'Nuevo servicio' }}</h3>
        <UFormField label="Nombre" :error="errors.name">
          <UInput v-model="name" v-bind="nameA" />
        </UFormField>
        <UFormField label="Descripción">
          <UTextarea v-model="description" v-bind="descA" :rows="2" />
        </UFormField>
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Duración (min)" :error="errors.duration">
            <UInput v-model="duration" v-bind="durA" type="number" min="5" step="5" />
          </UFormField>
          <UFormField label="Precio (MXN)" :error="errors.price">
            <UInput v-model="price" v-bind="priceA" type="number" min="0" step="0.01" />
          </UFormField>
        </div>
        <UFormField label="Color">
          <div class="flex gap-3 items-center">
            <input v-model="color" v-bind="colorA" type="color" class="h-9 w-14 rounded cursor-pointer border border-gray-200" />
            <UInput v-model="color" class="flex-1" />
          </div>
        </UFormField>

        <UFormField label="Doctores que ofrecen este servicio">
          <div v-if="loadingDoctors" class="text-xs text-gray-500 py-2">Cargando…</div>
          <div v-else-if="doctors.length === 0" class="text-xs text-gray-500 py-2">No hay doctores activos.</div>
          <div v-else class="max-h-56 overflow-y-auto rounded-lg border border-gray-200 divide-y divide-gray-100">
            <label
              v-for="d in doctors"
              :key="d.id"
              class="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50"
            >
              <input
                type="checkbox"
                :checked="(doctorIds ?? []).includes(d.id)"
                class="rounded border-gray-300 text-primary focus:ring-primary"
                @change="toggleDoctor(d.id)"
              />
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-slate-800 truncate">{{ d.full_name }}</p>
                <p class="text-xs text-gray-500 truncate">{{ d.specialty || 'Sin especialidad' }}</p>
              </div>
            </label>
          </div>
          <p class="text-xs text-gray-500 mt-1">
            Si dejás vacío, ningún doctor ofrecerá este servicio (no aparecerá en agendar).
          </p>
        </UFormField>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="open = false">Cancelar</UButton>
          <UButton type="submit" :loading="loading">Guardar</UButton>
        </div>
      </form>
    </template>
  </UModal>
</template>
