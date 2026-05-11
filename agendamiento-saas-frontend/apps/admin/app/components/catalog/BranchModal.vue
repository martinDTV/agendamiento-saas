<script setup lang="ts">
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import type { Branch } from '@agendamiento/shared'

const props = defineProps<{ branch: Branch | null }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>('open')

const { apiFetch } = useApi()
const toast = useToast()

const schema = toTypedSchema(z.object({
  name: z.string().min(1, 'Requerido'),
  address: z.string().optional().default(''),
  phone: z.string().optional().default('')
}))

const { handleSubmit, errors, defineField, resetForm } = useForm({ validationSchema: schema })
const [name, nameA] = defineField('name')
const [address, addressA] = defineField('address')
const [phone, phoneA] = defineField('phone')

watch(open, val => {
  if (val) resetForm({ values: { name: props.branch?.name ?? '', address: props.branch?.address ?? '', phone: props.branch?.phone ?? '' } })
})

const loading = ref(false)
const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    props.branch
      ? await apiFetch(`/catalog/branches/${props.branch.id}/`, { method: 'PATCH', body: values })
      : await apiFetch('/catalog/branches/', { method: 'POST', body: values })
    toast.add({ title: props.branch ? 'Sucursal actualizada' : 'Sucursal creada', color: 'primary' })
    open.value = false
    emit('saved')
  }
  catch { toast.add({ title: 'Error al guardar', color: 'error' }) }
  finally { loading.value = false }
})
</script>

<template>
  <UModal v-model:open="open" :title="branch ? 'Editar sucursal' : 'Nueva sucursal'">
    <template #content>
      <form class="space-y-4 p-6" @submit.prevent="onSubmit">
        <h3 class="text-base font-semibold text-slate-800">{{ branch ? 'Editar sucursal' : 'Nueva sucursal' }}</h3>
        <UFormField label="Nombre" :error="errors.name">
          <UInput v-model="name" v-bind="nameA" />
        </UFormField>
        <UFormField label="Dirección" :error="errors.address">
          <UInput v-model="address" v-bind="addressA" />
        </UFormField>
        <UFormField label="Teléfono" :error="errors.phone">
          <UInput v-model="phone" v-bind="phoneA" />
        </UFormField>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="open = false">Cancelar</UButton>
          <UButton type="submit" :loading="loading">Guardar</UButton>
        </div>
      </form>
    </template>
  </UModal>
</template>
