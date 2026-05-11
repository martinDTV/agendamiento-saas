<script setup lang="ts">
import type { Doctor, Branch } from '@agendamiento/shared'

const props = defineProps<{ doctor: Doctor | null; branches: Branch[] }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>('open')

const { apiFetch } = useApi()
const toast = useToast()

const form = reactive({
  first_name:           '',
  last_name:            '',
  email:                '',
  password:             '',
  role:                 'doctor' as 'doctor' | 'admin',
  specialty:            '',
  bio:                  '',
  appointment_duration: 30,
  branch:               null as string | null,
  is_active:            true,
})

const photoFile = ref<any>(null)
const photoPreview = ref<string | null>(null)
const removePhoto = ref(false)

function onPhotoChange(e: any) {
  const file = e?.target?.files?.[0]
  if (!file) return
  photoFile.value = file
  removePhoto.value = false
  const reader = new FileReader()
  reader.onload = (ev: any) => { photoPreview.value = ev?.target?.result ?? null }
  reader.readAsDataURL(file)
}

function clearPhoto() {
  photoFile.value = null
  photoPreview.value = null
  removePhoto.value = true
}

const NO_BRANCH = '__none__'
const branchItems = computed(() => [
  { label: 'Sin sucursal', value: NO_BRANCH },
  ...props.branches.map(b => ({ label: b.name, value: b.id })),
])

const roleItems = [
  { label: 'Doctor — atiende pacientes',  value: 'doctor' },
  { label: 'Admin — gestiona la clínica', value: 'admin'  },
]

const isEdit = computed(() => !!props.doctor)

watch(open, (val) => {
  if (!val) return
  photoFile.value = null
  removePhoto.value = false
  if (props.doctor) {
    const [first, ...rest] = (props.doctor.full_name ?? '').split(' ')
    form.first_name = first ?? ''
    form.last_name  = rest.join(' ')
    form.email      = props.doctor.email ?? ''
    form.password   = ''
    form.role       = 'doctor'
    form.specialty  = props.doctor.specialty ?? ''
    form.bio        = props.doctor.bio ?? ''
    form.appointment_duration = props.doctor.appointment_duration ?? 30
    form.branch     = props.doctor.branch ?? NO_BRANCH
    form.is_active  = props.doctor.is_active ?? true
    photoPreview.value = props.doctor.photo ?? null
  } else {
    form.first_name = ''
    form.last_name  = ''
    form.email      = ''
    form.password   = ''
    form.role       = 'doctor'
    form.specialty  = ''
    form.bio        = ''
    form.appointment_duration = 30
    form.branch     = NO_BRANCH
    form.is_active  = true
    photoPreview.value = null
  }
})

const loading = ref(false)

async function onSubmit() {
  if (!form.email) return toast.add({ title: 'Email es requerido', color: 'error' })
  if (!isEdit.value && !form.password) return toast.add({ title: 'Contraseña es requerida', color: 'error' })
  if (!isEdit.value && form.password.length < 8) return toast.add({ title: 'Contraseña mínimo 8 caracteres', color: 'error' })

  loading.value = true
  try {
    const hasFileChange = photoFile.value !== null || removePhoto.value
    if (isEdit.value) {
      const editFields = {
        specialty: form.specialty,
        bio: form.bio,
        appointment_duration: form.appointment_duration,
        branch: form.branch && form.branch !== NO_BRANCH ? form.branch : null,
        is_active: form.is_active,
      }
      let body: any = editFields
      if (hasFileChange) {
        const fd = new FormData()
        fd.append('specialty', editFields.specialty ?? '')
        fd.append('bio', editFields.bio ?? '')
        fd.append('appointment_duration', String(editFields.appointment_duration))
        if (editFields.branch) fd.append('branch', editFields.branch)
        fd.append('is_active', String(editFields.is_active))
        if (photoFile.value) fd.append('photo', photoFile.value)
        else if (removePhoto.value) fd.append('photo', '')
        body = fd
      }
      await apiFetch(`/catalog/doctors/${props.doctor!.id}/`, { method: 'PATCH', body })
    } else {
      const createFields: Record<string, any> = {
        email:                form.email,
        password:             form.password,
        first_name:           form.first_name,
        last_name:            form.last_name,
        role:                 form.role,
        specialty:            form.specialty,
        bio:                  form.bio,
        appointment_duration: form.appointment_duration,
        branch:               form.branch && form.branch !== NO_BRANCH ? form.branch : null,
        is_active:            form.is_active,
      }
      let body: any = createFields
      if (photoFile.value) {
        const fd = new FormData()
        for (const [k, v] of Object.entries(createFields)) {
          if (v === null || v === undefined) continue
          fd.append(k, String(v))
        }
        fd.append('photo', photoFile.value)
        body = fd
      }
      await apiFetch('/catalog/doctors/', { method: 'POST', body })
    }
    toast.add({ title: 'Guardado', color: 'primary' })
    open.value = false
    emit('saved')
  } catch (err: any) {
    const msg = err?.response?.data?.detail
            ?? err?.response?.data?.email?.[0]
            ?? err?.response?.data?.error
            ?? 'Error al guardar'
    toast.add({ title: msg, color: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal v-model:open="open" :title="isEdit ? 'Editar doctor' : 'Nuevo miembro'">
    <template #content>
      <form class="flex flex-col max-h-[85vh]" @submit.prevent="onSubmit">
        <div class="flex-1 overflow-y-auto px-6 pt-6 pb-4 space-y-4">
        <h3 class="text-base font-semibold text-slate-800">{{ isEdit ? 'Editar doctor' : 'Nuevo miembro' }}</h3>

        <!-- New: role + login credentials -->
        <template v-if="!isEdit">
          <UFormField label="Rol">
            <USelect
              v-model="form.role"
              :items="roleItems"
              value-attribute="value"
              label-attribute="label"
              class="w-full"
            />
          </UFormField>

          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Nombre">
              <UInput v-model="form.first_name" />
            </UFormField>
            <UFormField label="Apellido">
              <UInput v-model="form.last_name" />
            </UFormField>
          </div>

          <UFormField label="Correo de inicio de sesión">
            <UInput v-model="form.email" type="email" placeholder="doctor@clinica.com" />
          </UFormField>

          <UFormField label="Contraseña inicial" hint="Mínimo 8 caracteres">
            <UInput v-model="form.password" type="password" autocomplete="new-password" />
          </UFormField>
        </template>

        <!-- Edit: show email read-only -->
        <UFormField v-else label="Email">
          <UInput :model-value="form.email" disabled />
        </UFormField>

        <!-- Doctor-only fields (hidden if creating an admin) -->
        <template v-if="form.role === 'doctor' || isEdit">
          <div>
            <p class="text-sm font-medium text-slate-700 mb-1.5">Foto del doctor</p>
            <div class="flex items-center gap-4">
              <div class="w-20 h-20 rounded-full overflow-hidden bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center flex-shrink-0 ring-1 ring-slate-200 dark:ring-slate-700">
                <img v-if="photoPreview" :src="photoPreview" class="w-full h-full object-cover" alt="">
                <UIcon v-else name="i-lucide-user" class="w-8 h-8 text-violet-500" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="inline-flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg ring-1 ring-slate-200 dark:ring-slate-700 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 w-fit">
                  <UIcon name="i-lucide-upload" class="w-4 h-4" />
                  <span>{{ photoPreview ? 'Cambiar foto' : 'Subir foto' }}</span>
                  <input type="file" accept="image/*" class="hidden" @change="onPhotoChange">
                </label>
                <button
                  v-if="photoPreview"
                  type="button"
                  class="text-xs text-rose-600 hover:underline w-fit"
                  @click="clearPhoto"
                >
                  Quitar foto
                </button>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Especialidad">
              <UInput v-model="form.specialty" placeholder="Ej. Cardiología" />
            </UFormField>
            <UFormField label="Duración cita (min)">
              <UInput v-model.number="form.appointment_duration" type="number" min="5" step="5" />
            </UFormField>
          </div>
          <UFormField label="Sucursal">
            <USelect
              v-model="form.branch"
              :items="branchItems"
              value-attribute="value"
              label-attribute="label"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Biografía">
            <UTextarea v-model="form.bio" :rows="3" />
          </UFormField>
        </template>

        <UFormField label="Activo">
          <USwitch v-model="form.is_active" />
        </UFormField>
        </div>

        <!-- Footer sticky -->
        <div class="flex justify-end gap-2 px-6 py-4 border-t bg-white" style="border-color: #F3F4F6;">
          <UButton variant="ghost" color="neutral" @click="open = false">Cancelar</UButton>
          <UButton type="submit" :loading="loading">Guardar</UButton>
        </div>
      </form>
    </template>
  </UModal>
</template>
