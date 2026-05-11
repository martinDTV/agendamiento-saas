<script setup lang="ts">
const emit = defineEmits<{ created: [] }>()
const open = defineModel<boolean>('open')

const { apiFetch } = useApi()
const toast = useToast()

const form = reactive({
  name: '',
  slug: '',
  type: 'clinic' as 'clinic' | 'doctor' | 'doctor_assistant',
  admin_email: '',
  admin_first_name: '',
  admin_last_name: ''
})

const typeItems = [
  { label: 'Clínica (multi-doctor)', value: 'clinic' },
  { label: 'Doctor solo', value: 'doctor' },
  { label: 'Doctor + asistente', value: 'doctor_assistant' }
]

const loading = ref(false)
const slugTouched = ref(false)

watch(() => form.name, (val) => {
  if (slugTouched.value) return
  form.slug = val
    .toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
})

watch(open, (val) => {
  if (!val) return
  form.name = ''
  form.slug = ''
  form.type = 'clinic'
  form.admin_email = ''
  form.admin_first_name = ''
  form.admin_last_name = ''
  slugTouched.value = false
})

async function onSubmit() {
  if (!form.name.trim()) return toast.add({ title: 'Nombre requerido', color: 'error' })
  if (!form.slug.trim()) return toast.add({ title: 'Slug requerido', color: 'error' })
  if (!/^[a-z0-9-]+$/.test(form.slug)) return toast.add({ title: 'Slug solo con minúsculas, números y guiones', color: 'error' })
  if (!form.admin_email.trim()) return toast.add({ title: 'Email del admin requerido', color: 'error' })

  loading.value = true
  try {
    await apiFetch('/platform/tenants/', { method: 'POST', body: form })
    toast.add({
      title: '¡Tenant creado!',
      description: `Se envió un correo de activación a ${form.admin_email}`,
      color: 'primary'
    })
    open.value = false
    emit('created')
  }
  catch (err: any) {
    const msg = err?.response?.data?.detail
            ?? err?.response?.data?.error
            ?? 'Error al crear el tenant'
    toast.add({ title: msg, color: 'error' })
  }
  finally { loading.value = false }
}
</script>

<template>
  <UModal v-model:open="open" title="Nuevo tenant">
    <template #content>
      <form class="space-y-4 p-6" @submit.prevent="onSubmit">
        <h3 class="text-base font-semibold text-slate-800">Nuevo tenant</h3>
        <p class="text-xs text-slate-500 -mt-2">
          Se creará el tenant en plan <strong>Free</strong> y se enviará un correo al admin con
          la contraseña temporal y el enlace de activación.
        </p>

        <UFormField label="Nombre de la clínica/práctica">
          <UInput v-model="form.name" placeholder="Ej. Clínica del Norte" autofocus />
        </UFormField>

        <UFormField label="Slug" hint="Subdominio del tenant — será {slug}.miapp.com">
          <UInput v-model="form.slug" placeholder="clinica-del-norte" @input="slugTouched = true" />
        </UFormField>

        <UFormField label="Tipo">
          <USelect v-model="form.type" :items="typeItems" value-attribute="value" label-attribute="label" class="w-full" />
        </UFormField>

        <div class="pt-2 border-t" style="border-color: #F3F4F6;">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2 mt-3">Admin del tenant</p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <UFormField label="Nombre">
            <UInput v-model="form.admin_first_name" />
          </UFormField>
          <UFormField label="Apellido">
            <UInput v-model="form.admin_last_name" />
          </UFormField>
        </div>

        <UFormField label="Email">
          <UInput v-model="form.admin_email" type="email" placeholder="admin@clinicadelnorte.com" />
        </UFormField>

        <div class="flex justify-end gap-2 pt-2 border-t" style="border-color: #F3F4F6;">
          <UButton variant="ghost" color="neutral" @click="open = false">Cancelar</UButton>
          <UButton type="submit" :loading="loading">Crear y enviar correo</UButton>
        </div>
      </form>
    </template>
  </UModal>
</template>
