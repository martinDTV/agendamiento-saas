<script setup>
useSeoMeta({
  title: 'Funciones — NexoSoftDev',
  description: 'Todas las funciones de NexoSoftDev: WhatsApp, dominio propio, página editable, agenda en línea, multi-doctor y más.'
})

const { open: openLead } = useLeadModal()
const DEMO_URL = 'https://demo-agendamiento.nexosoftdev.com'

const groups = [
  {
    title: 'Reduce inasistencias',
    icon: 'i-lucide-message-circle',
    items: [
      { title: 'Recordatorios por WhatsApp', desc: 'Confirmaciones automáticas antes de cada cita, sin llamadas manuales.' },
      { title: 'Recordatorios por correo', desc: 'Refuerza la confirmación por un segundo canal.' },
      { title: 'Reagenda y cancelación en línea', desc: 'El paciente reprograma desde el mismo enlace, liberando el hueco.' }
    ]
  },
  {
    title: 'Tu presencia en línea',
    icon: 'i-lucide-globe',
    items: [
      { title: 'Tu propio dominio', desc: 'Tus pacientes agendan desde tuconsultorio.com; la marca es tuya.' },
      { title: 'Página editable (CMS)', desc: 'Edita textos, servicios, horarios e imágenes desde el panel, sin código.' },
      { title: 'Página de reservas 24/7', desc: 'Tus pacientes reservan a cualquier hora del día.' }
    ]
  },
  {
    title: 'Agenda y operación',
    icon: 'i-lucide-calendar-clock',
    items: [
      { title: 'Agenda configurable', desc: 'Horarios por doctor, servicio y sucursal; bloquea descansos y define duraciones.' },
      { title: 'Multi-doctor y sucursales', desc: 'Coordina varios médicos y ubicaciones desde un panel central.' },
      { title: 'Catálogo de servicios', desc: 'Define servicios, duraciones y precios por consultorio.' }
    ]
  },
  {
    title: 'Control y seguridad',
    icon: 'i-lucide-shield-check',
    items: [
      { title: 'Reportes y estadísticas', desc: 'Ingresos, ocupación y tasas de cancelación, exportables a Excel.' },
      { title: 'Permisos por rol', desc: 'Controla quién ve y edita qué dentro de tu equipo.' },
      { title: 'Datos resguardados', desc: 'Información de pacientes con respaldos y control de acceso.' }
    ]
  }
]
</script>

<template>
  <UContainer class="py-16 sm:py-24">
    <div class="max-w-2xl">
      <h1 class="text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
        Todo lo que tu consultorio necesita
      </h1>
      <p class="mt-4 text-lg leading-relaxed text-muted">
        Validado con doctores reales. Sin funciones de relleno: cada herramienta
        existe para que recibas más pacientes y pierdas menos citas.
      </p>
    </div>

    <div class="mt-14 space-y-14">
      <section v-for="(g, i) in groups" :key="i">
        <div class="flex items-center gap-3">
          <span class="flex size-9 items-center justify-center rounded-lg bg-primary/10">
            <UIcon :name="g.icon" class="size-5 text-primary" />
          </span>
          <h2 class="text-xl font-medium text-highlighted">
            {{ g.title }}
          </h2>
        </div>
        <div class="mt-6 grid gap-4 md:grid-cols-3">
          <div
            v-for="(item, j) in g.items"
            :key="j"
            class="rounded-2xl border border-default p-6"
          >
            <h3 class="font-medium text-highlighted">
              {{ item.title }}
            </h3>
            <p class="mt-2 text-sm text-muted">
              {{ item.desc }}
            </p>
          </div>
        </div>
      </section>
    </div>

    <!-- CTA -->
    <div class="mt-16 flex flex-col items-start gap-4 rounded-2xl bg-elevated/40 border border-default p-8 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-lg font-medium text-highlighted">
          Pruébalo con datos de ejemplo
        </h2>
        <p class="text-sm text-muted">
          Explora el panel real en la demo, sin registrarte.
        </p>
      </div>
      <div class="flex gap-2">
        <UButton :to="DEMO_URL" target="_blank" trailing-icon="i-lucide-arrow-right">
          Probar la demo
        </UButton>
        <UButton color="neutral" variant="subtle" @click="openLead('')">
          Solicitar información
        </UButton>
      </div>
    </div>
  </UContainer>
</template>
