<script setup>
const features = [
  {
    icon: 'i-lucide-message-circle',
    title: 'Recordatorios por WhatsApp',
    description: 'Confirmaciones automáticas antes de cada cita. Menos inasistencias, sin llamadas manuales de tu recepción.'
  },
  {
    icon: 'i-lucide-globe',
    title: 'Tu propio dominio',
    description: 'Tus pacientes agendan desde tuconsultorio.com. La marca es tuya; nosotros solo ponemos la infraestructura.'
  },
  {
    icon: 'i-lucide-layout-template',
    title: 'Página editable',
    description: 'Edita textos, servicios, horarios e imágenes desde el panel. Sin tocar código y sin depender de nadie.'
  },
  {
    icon: 'i-lucide-calendar-clock',
    title: 'Agenda en línea 24/7',
    description: 'Tus pacientes reservan a cualquier hora. Tú defines la disponibilidad por doctor, servicio y sucursal.'
  },
  {
    icon: 'i-lucide-users',
    title: 'Multi-doctor y sucursales',
    description: 'Coordina varios médicos y ubicaciones desde un panel central, con permisos por rol.'
  },
  {
    icon: 'i-lucide-shield-check',
    title: 'Datos resguardados',
    description: 'Información de pacientes con respaldos y control de acceso. Construido para el contexto clínico mexicano.'
  }
]

const steps = [
  {
    step: '01',
    title: 'Crea tu cuenta',
    description: 'Registra tu consultorio en minutos. Sin tarjeta para empezar.'
  },
  {
    step: '02',
    title: 'Configura tu agenda',
    description: 'Define doctores, servicios, horarios y conecta tu dominio.'
  },
  {
    step: '03',
    title: 'Recibe pacientes',
    description: 'Comparte tu liga de reservas y deja que WhatsApp confirme por ti.'
  }
]

const useCases = [
  {
    icon: 'i-lucide-stethoscope',
    title: 'Médico independiente',
    description: 'Una agenda limpia, recordatorios automáticos y una página propia sin contratar a un desarrollador.'
  },
  {
    icon: 'i-lucide-building-2',
    title: 'Clínica con varios doctores',
    description: 'Coordina especialidades, sucursales y horarios desde un panel central con reportes por médico.'
  },
  {
    icon: 'i-lucide-heart-pulse',
    title: 'Consultorio en crecimiento',
    description: 'Empieza gratis y sube de plan cuando lo necesites. La herramienta crece contigo.'
  }
]

const testimonials = [
  {
    quote: 'Bajaron las inasistencias notablemente desde que los recordatorios salen solos por WhatsApp.',
    name: 'Dra. Laura M.',
    role: 'Medicina general',
    avatar: { icon: 'i-lucide-user' }
  },
  {
    quote: 'Por fin tengo mi propia página de citas con mi dominio, sin depender de nadie para editarla.',
    name: 'Dr. Ricardo S.',
    role: 'Dermatología',
    avatar: { icon: 'i-lucide-user' }
  },
  {
    quote: 'Manejamos tres doctores en dos sucursales desde un solo lugar. Nos ahorró muchísimas llamadas.',
    name: 'Clínica Vértice',
    role: 'Recepción',
    avatar: { icon: 'i-lucide-user' }
  }
]

const plans = [
  {
    title: 'Gratuito',
    description: 'Para empezar y probar sin compromiso.',
    price: '$0',
    billing: 'MXN / mes',
    features: [
      'Hasta 2 doctores',
      '50 citas al mes',
      '1 sucursal',
      'Recordatorios por correo',
      'Agenda en línea'
    ],
    button: { label: 'Empezar gratis', color: 'neutral', variant: 'subtle' }
  },
  {
    title: 'Profesional',
    description: 'Para el consultorio que quiere reducir inasistencias.',
    price: '$549',
    billing: 'MXN / mes',
    highlight: true,
    badge: 'Más popular',
    features: [
      'Hasta 3 doctores',
      '500 citas al mes',
      'Recordatorios por WhatsApp (300 incluidos)',
      'Tu propio dominio',
      'Página editable (CMS)',
      'Reportes básicos'
    ],
    button: { label: 'Elegir Profesional' }
  },
  {
    title: 'Clínica',
    description: 'Para varios doctores y sucursales.',
    price: '$1,299',
    billing: 'MXN / mes',
    features: [
      'Hasta 10 doctores',
      '2,500 citas al mes',
      'Hasta 5 sucursales',
      'WhatsApp (1,000 incluidos)',
      'Reportes avanzados',
      'Soporte prioritario'
    ],
    button: { label: 'Elegir Clínica', color: 'neutral', variant: 'subtle' }
  }
]
</script>

<template>
  <div>
    <!-- 1. HERO — split, product panel right -->
    <UPageHero
      :ui="{ container: 'py-20 sm:py-28 lg:py-32' }"
    >
      <template #headline>
        <UBadge
          color="secondary"
          variant="subtle"
          class="rounded-full"
          label="Software en producción, no en presentación"
        />
      </template>

      <template #title>
        <span class="block">Agenda médica con</span>
        <span class="block text-primary">recordatorios por WhatsApp</span>
      </template>

      <template #description>
        Reduce las inasistencias en tu consultorio. Agenda en línea, tu propio dominio
        y una página de reservas para tus pacientes. Construido y desplegado por NexoSoftDev,
        hecho para México.
      </template>

      <template #links>
        <UButton
          label="Prueba gratis"
          to="#precios"
          size="xl"
          trailing-icon="i-lucide-arrow-right"
        />
        <UButton
          label="Ver cómo funciona"
          to="#como-funciona"
          size="xl"
          color="neutral"
          variant="subtle"
        />
        <p class="basis-full text-sm text-muted mt-2">
          Sin tarjeta para empezar · Cancela cuando quieras
        </p>
      </template>

      <!-- Product mock: booking confirmation + WhatsApp reminder -->
      <div class="relative">
        <div class="absolute -inset-4 bg-primary/10 blur-2xl rounded-3xl" />
        <div class="relative rounded-2xl border border-default bg-default shadow-xl overflow-hidden">
          <div class="flex items-center gap-1.5 px-4 py-3 border-b border-default bg-elevated/50">
            <span class="size-2.5 rounded-full bg-error/60" />
            <span class="size-2.5 rounded-full bg-warning/60" />
            <span class="size-2.5 rounded-full bg-success/60" />
            <span class="ml-2 text-xs text-muted">app.tuconsultorio.com</span>
          </div>
          <div class="p-5 space-y-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-highlighted">
                Agenda — Hoy
              </p>
              <UBadge color="primary" variant="subtle" label="3 citas" />
            </div>

            <div
              v-for="(t, i) in [
                { h: '09:00', n: 'Ana Robles', s: 'Consulta general', c: 'success' },
                { h: '10:30', n: 'Carlos Méndez', s: 'Seguimiento', c: 'primary' },
                { h: '12:00', n: 'María Luna', s: 'Primera vez', c: 'warning' }
              ]"
              :key="i"
              class="flex items-center gap-3 rounded-lg border border-default p-3"
            >
              <div class="text-xs font-medium text-muted w-12 tabular-nums">
                {{ t.h }}
              </div>
              <div class="size-8 rounded-full bg-elevated flex items-center justify-center">
                <UIcon name="i-lucide-user" class="size-4 text-dimmed" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-highlighted truncate">
                  {{ t.n }}
                </p>
                <p class="text-xs text-muted truncate">
                  {{ t.s }}
                </p>
              </div>
              <UBadge :color="t.c" variant="subtle" size="sm" label="Confirmada" />
            </div>

            <div class="flex items-start gap-3 rounded-lg bg-primary/10 p-3">
              <UIcon name="i-lucide-message-circle" class="size-5 text-primary shrink-0 mt-0.5" />
              <p class="text-xs text-default leading-relaxed">
                <span class="font-semibold">WhatsApp enviado:</span>
                «Hola Ana, te recordamos tu cita mañana a las 9:00. Responde
                <span class="font-semibold">1</span> para confirmar.»
              </p>
            </div>
          </div>
        </div>
      </div>
    </UPageHero>

    <!-- 2. TRUST BAR -->
    <UContainer>
      <USeparator />
      <div class="py-8 flex flex-col items-center gap-5">
        <p class="text-xs uppercase tracking-widest text-muted">
          Diseñado para el flujo real de un consultorio mexicano
        </p>
        <div class="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 text-muted">
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-message-circle" class="size-5" /> WhatsApp Business
          </span>
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-globe" class="size-5" /> Dominio propio
          </span>
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-credit-card" class="size-5" /> Pagos en MXN
          </span>
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-smartphone" class="size-5" /> App para pacientes
          </span>
        </div>
      </div>
      <USeparator />
    </UContainer>

    <!-- 3. FEATURES — bento grid -->
    <UPageSection
      id="funciones"
      title="Lo que tu consultorio necesita, sin sobrar"
      description="Las tres cosas que validamos con doctores reales — WhatsApp, dominio propio y página editable — más la agenda que las integra."
    >
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <UPageCard
          v-for="(f, i) in features"
          :key="i"
          :icon="f.icon"
          :title="f.title"
          :description="f.description"
          variant="subtle"
        />
      </div>
    </UPageSection>

    <!-- 4. PRODUCT SHOWCASE — calendar mock, text right -->
    <UContainer>
      <div class="rounded-3xl bg-elevated/40 border border-default p-6 sm:p-10 lg:p-14">
        <div class="grid lg:grid-cols-2 gap-10 items-center">
          <!-- calendar mock -->
          <div class="rounded-2xl border border-default bg-default p-5 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <p class="text-sm font-semibold text-highlighted">
                Disponibilidad — Dra. Laura M.
              </p>
              <div class="flex gap-1">
                <UButton icon="i-lucide-chevron-left" size="xs" color="neutral" variant="ghost" />
                <UButton icon="i-lucide-chevron-right" size="xs" color="neutral" variant="ghost" />
              </div>
            </div>
            <div class="grid grid-cols-4 gap-2">
              <div
                v-for="(slot, i) in [
                  '09:00', '09:30', '10:00', '10:30',
                  '11:00', '11:30', '12:00', '12:30',
                  '16:00', '16:30', '17:00', '17:30'
                ]"
                :key="i"
                class="rounded-lg border text-center text-xs py-2.5 font-medium"
                :class="[2, 5, 9].includes(i)
                  ? 'border-default bg-elevated text-dimmed line-through'
                  : 'border-primary/30 bg-primary/10 text-primary'"
              >
                {{ slot }}
              </div>
            </div>
            <div class="mt-4 flex items-center gap-4 text-xs text-muted">
              <span class="inline-flex items-center gap-1.5">
                <span class="size-2.5 rounded-sm bg-primary/40" /> Disponible
              </span>
              <span class="inline-flex items-center gap-1.5">
                <span class="size-2.5 rounded-sm bg-elevated border border-default" /> Ocupado
              </span>
            </div>
          </div>

          <!-- text -->
          <div class="space-y-5">
            <UBadge color="secondary" variant="subtle" label="Agenda configurable" />
            <h2 class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
              Tú defines las reglas, el sistema llena la agenda
            </h2>
            <p class="text-muted">
              Configura horarios por doctor y por servicio. Bloquea descansos, define
              duraciones y deja que tus pacientes reserven solo en los huecos reales.
              Cada confirmación dispara el recordatorio por WhatsApp automáticamente.
            </p>
            <ul class="space-y-3">
              <li
                v-for="(item, i) in [
                  'Horarios por doctor, servicio y sucursal',
                  'Confirmación y recordatorio automáticos',
                  'Reagenda y cancelación desde el mismo enlace'
                ]"
                :key="i"
                class="flex items-start gap-3 text-sm text-default"
              >
                <UIcon name="i-lucide-check-circle-2" class="size-5 text-primary shrink-0" />
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </UContainer>

    <!-- 5. HOW IT WORKS / USE CASES -->
    <UPageSection
      id="como-funciona"
      title="Empieza en tres pasos"
      description="De cero a recibir pacientes en línea el mismo día."
    >
      <div class="grid gap-6 md:grid-cols-3">
        <div
          v-for="(s, i) in steps"
          :key="i"
          class="relative rounded-2xl border border-default p-6"
        >
          <span class="text-5xl font-semibold text-primary/20 tabular-nums">{{ s.step }}</span>
          <h3 class="mt-3 text-lg font-semibold text-highlighted">
            {{ s.title }}
          </h3>
          <p class="mt-2 text-sm text-muted">
            {{ s.description }}
          </p>
        </div>
      </div>

      <div id="casos" class="grid gap-4 md:grid-cols-3 mt-12">
        <UPageCard
          v-for="(c, i) in useCases"
          :key="i"
          :icon="c.icon"
          :title="c.title"
          :description="c.description"
          spotlight
        />
      </div>
    </UPageSection>

    <!-- 6. TESTIMONIALS -->
    <UPageSection
      title="Doctores que ya dejaron de perseguir confirmaciones"
      :ui="{ container: 'py-16 sm:py-20' }"
    >
      <div class="grid gap-4 md:grid-cols-3">
        <UPageCard
          v-for="(t, i) in testimonials"
          :key="i"
          variant="subtle"
        >
          <div class="space-y-4">
            <UIcon name="i-lucide-quote" class="size-6 text-primary/40" />
            <p class="text-default leading-relaxed">
              {{ t.quote }}
            </p>
            <div class="flex items-center gap-3 pt-2">
              <div class="size-9 rounded-full bg-elevated flex items-center justify-center">
                <UIcon name="i-lucide-user" class="size-4 text-dimmed" />
              </div>
              <div>
                <p class="text-sm font-medium text-highlighted">
                  {{ t.name }}
                </p>
                <p class="text-xs text-muted">
                  {{ t.role }}
                </p>
              </div>
            </div>
          </div>
        </UPageCard>
      </div>
    </UPageSection>

    <!-- 7. PRICING -->
    <UPageSection
      id="precios"
      title="Precios claros, en pesos"
      description="Empieza gratis. Sube de plan cuando tu consultorio lo pida. Sin contratos forzosos."
    >
      <div class="grid gap-6 lg:grid-cols-3 items-stretch">
        <div
          v-for="(p, i) in plans"
          :key="i"
          class="relative flex flex-col rounded-2xl border p-6"
          :class="p.highlight ? 'border-primary ring-1 ring-primary shadow-lg' : 'border-default'"
        >
          <UBadge
            v-if="p.badge"
            :label="p.badge"
            color="secondary"
            class="absolute -top-3 left-6"
          />
          <h3 class="text-lg font-semibold text-highlighted">
            {{ p.title }}
          </h3>
          <p class="mt-1 text-sm text-muted min-h-10">
            {{ p.description }}
          </p>
          <div class="mt-4 flex items-baseline gap-1.5">
            <span class="text-4xl font-semibold text-highlighted tracking-tight">{{ p.price }}</span>
            <span class="text-sm text-muted">{{ p.billing }}</span>
          </div>
          <UButton
            class="mt-5 justify-center"
            block
            v-bind="p.button"
            to="https://app.nexosoftdev.com/registro"
          />
          <USeparator class="my-5" />
          <ul class="space-y-3 flex-1">
            <li
              v-for="(feat, j) in p.features"
              :key="j"
              class="flex items-start gap-2.5 text-sm text-default"
            >
              <UIcon name="i-lucide-check" class="size-4 text-primary shrink-0 mt-0.5" />
              {{ feat }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Enterprise strip -->
      <div class="mt-6 rounded-2xl border border-default bg-elevated/40 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 class="text-base font-semibold text-highlighted">
            ¿Cadena de clínicas o necesidades especiales?
          </h3>
          <p class="text-sm text-muted">
            Doctores y citas ilimitados, white-label e integraciones a la medida.
          </p>
        </div>
        <UButton
          label="Contactar ventas"
          color="neutral"
          variant="subtle"
          trailing-icon="i-lucide-arrow-right"
          to="#"
        />
      </div>
    </UPageSection>

    <!-- 8. FINAL CTA -->
    <UPageSection>
      <UPageCTA
        title="Tu agenda en producción, no en presentación"
        description="Crea tu cuenta gratis y empieza a recibir reservas en línea hoy mismo. Sin tarjeta, sin instalaciones, sin sorpresas en la factura."
        variant="subtle"
        :links="[{
          label: 'Crear cuenta gratis',
          to: 'https://app.nexosoftdev.com/registro',
          trailingIcon: 'i-lucide-arrow-right',
          size: 'xl'
        }, {
          label: 'Hablar con nosotros',
          to: '#',
          color: 'neutral',
          variant: 'outline',
          size: 'xl'
        }]"
      />
    </UPageSection>
  </div>
</template>
