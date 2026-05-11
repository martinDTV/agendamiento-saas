<script setup lang="ts">
const props = defineProps<{ error: { statusCode: number; message: string } }>()

const handle = () => clearError({ redirect: '/' })
</script>

<template>
  <UApp>
    <div class="min-h-screen bg-[#FAFAF7] flex flex-col items-center justify-center gap-6 text-center px-4">
      <p class="text-6xl font-bold text-gray-200">{{ props.error.statusCode }}</p>
      <h1 class="text-xl font-semibold text-gray-800">
        {{ props.error.statusCode === 404 ? 'Página no encontrada' : 'Algo salió mal' }}
      </h1>
      <p class="text-gray-500 max-w-sm">{{ props.error.message }}</p>
      <UButton @click="handle" variant="outline">
        Volver al inicio
      </UButton>
    </div>
  </UApp>
</template>
