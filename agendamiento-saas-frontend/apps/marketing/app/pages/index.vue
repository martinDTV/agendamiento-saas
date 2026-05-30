<script setup>
import { onMounted } from 'vue'

// Demo multiclínica desplegada en el Droplet (DigitalOcean).
const DEMO_URL = 'https://demo-agendamiento.nexosoftdev.com'

// Screenshots reales del panel (servidos desde CDN externo).
const SHOT_BASE = 'https://cloud-images-mdtv.web.app/images/nexosoftdev/agendamiento'
const shot = name => `${SHOT_BASE}/${name}-agendamiento-nexosoftdev.png`

const heroShot = shot('agenda')

// Galería del producto: capturas representativas del panel real.
const gallery = [
  { src: shot('agenda'), label: 'Agenda', caption: 'Vista semanal con citas por doctor y estado en tiempo real.' },
  { src: shot('doctores'), label: 'Doctores', caption: 'Administra tu equipo médico, especialidades y sucursales.' },
  { src: shot('servicios'), label: 'Servicios', caption: 'Define servicios, duraciones y precios por consultorio.' },
  { src: shot('configuracion-sitio-contenido'), label: 'Página editable', caption: 'Edita el contenido de tu página de reservas sin tocar código.' },
  { src: shot('juntas'), label: 'Juntas', caption: 'Agenda y coordina reuniones del equipo médico.' },
  { src: shot('sucursales'), label: 'Sucursales', caption: 'Coordina varias ubicaciones desde un panel central.' }
]
const galleryIndex = ref(0)

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

const { open: openLead } = useLeadModal()

const plans = [
  {
    slug: 'gratuito',
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
    button: { label: 'Solicitar información', color: 'neutral', variant: 'subtle' }
  },
  {
    slug: 'profesional',
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
    button: { label: 'Me interesa' }
  },
  {
    slug: 'clinica',
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
    button: { label: 'Solicitar información', color: 'neutral', variant: 'subtle' }
  }
]

// Hero entrance: a quick, sequenced reveal on first paint.
onMounted(async () => {
  if (import.meta.server) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

  const { gsap } = await import('gsap')
  const targets = Array.from(document.querySelectorAll('[data-hero]'))
  if (!targets.length) return

  gsap.set(targets, { opacity: 0, y: 24 })
  gsap.to(targets, {
    opacity: 1,
    y: 0,
    duration: 0.8,
    ease: 'power3.out',
    stagger: 0.12,
    delay: 0.1
  })
})
</script>

<template>
  <div>
    <!-- 1. HERO — split, product panel right, 3D particle backdrop -->
    <div class="relative overflow-hidden">
      <HeroSpotlight />
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-default" />
    <UPageHero
      class="relative"
      :ui="{ container: 'py-20 sm:py-28 lg:py-32' }"
    >
      <template #headline>
        <UBadge
          data-hero
          color="secondary"
          variant="subtle"
          class="rounded-full"
          label="Software en producción, no en presentación"
        />
      </template>

      <template #title>
        <span data-hero class="block">Agenda médica con</span>
        <span data-hero class="block text-primary">recordatorios por WhatsApp</span>
      </template>

      <template #description>
        <span data-hero class="block">
          Reduce las inasistencias en tu consultorio. Agenda en línea, tu propio dominio
          y una página de reservas para tus pacientes. Construido y desplegado por NexoSoftDev,
          hecho para México.
        </span>
      </template>

      <template #links>
        <UButton
          data-hero
          label="Prueba gratis"
          to="#precios"
          size="xl"
          trailing-icon="i-lucide-arrow-right"
        />
        <UButton
          data-hero
          label="Ver cómo funciona"
          to="#como-funciona"
          size="xl"
          color="neutral"
          variant="subtle"
        />
        <p data-hero class="basis-full text-sm text-muted mt-2">
          Sin tarjeta para empezar · Cancela cuando quieras
        </p>
      </template>

      <!-- Real product screenshot in our own browser frame -->
      <div data-hero v-parallax="-30" class="relative">
        <div class="absolute -inset-4 bg-primary/10 blur-2xl rounded-3xl" />
        <BrowserFrame
          :src="heroShot"
          alt="Agenda del panel de NexoSoftDev: vista semanal con citas por doctor"
          class="relative"
        />
        <!-- Floating WhatsApp accent -->
        <div class="absolute -bottom-5 -left-3 hidden max-w-xs items-start gap-3 rounded-xl border border-default bg-default p-3 shadow-lg sm:flex">
          <UIcon name="i-lucide-message-circle" class="size-5 text-primary shrink-0 mt-0.5" />
          <p class="text-xs text-default leading-relaxed">
            <span class="font-semibold">WhatsApp enviado:</span>
            «Hola Ana, te recordamos tu cita mañana a las 9:00. Responde
            <span class="font-semibold">1</span> para confirmar.»
          </p>
        </div>
      </div>
    </UPageHero>
    </div>

    <!-- 2. TRUST BAR -->
    <UContainer>
      <div v-reveal class="flex flex-col gap-6 border-y border-default py-7 sm:flex-row sm:items-center sm:justify-between">
        <p class="max-w-xs text-sm text-muted">
          Diseñado para el flujo real de un consultorio mexicano.
        </p>
        <div class="flex flex-wrap items-center gap-x-7 gap-y-3 text-default">
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-message-circle" class="size-4 text-primary" /> WhatsApp Business
          </span>
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-globe" class="size-4 text-primary" /> Dominio propio
          </span>
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-credit-card" class="size-4 text-primary" /> Pagos en MXN
          </span>
          <span class="inline-flex items-center gap-2 text-sm font-medium">
            <UIcon name="i-lucide-smartphone" class="size-4 text-primary" /> App para pacientes
          </span>
        </div>
      </div>
    </UContainer>

    <!-- 3. FEATURES — asymmetric bento -->
    <section id="funciones" class="py-20 sm:py-28">
      <UContainer>
        <div v-reveal class="max-w-2xl">
          <h2 class="text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
            Lo que tu consultorio necesita, sin sobrar
          </h2>
          <p class="mt-4 text-lg leading-relaxed text-muted">
            Las tres cosas que validamos con doctores reales (WhatsApp, dominio
            propio y página editable) más la agenda que las integra.
          </p>
        </div>

        <!-- Bento: rows of unequal weight, not six identical tiles -->
        <div class="mt-12 grid gap-4 md:grid-cols-6">
          <article
            v-reveal
            class="lift flex flex-col justify-between rounded-2xl border border-default bg-elevated/40 p-7 md:col-span-3 lg:col-span-4"
          >
            <UIcon :name="features[0].icon" class="size-7 text-primary" />
            <div class="mt-10">
              <h3 class="text-lg font-medium text-highlighted">
                {{ features[0].title }}
              </h3>
              <p class="mt-2 max-w-md text-muted">
                {{ features[0].description }}
              </p>
            </div>
          </article>

          <article
            v-reveal="80"
            class="lift flex flex-col justify-between rounded-2xl border border-default p-7 md:col-span-3 lg:col-span-2"
          >
            <UIcon :name="features[1].icon" class="size-7 text-primary" />
            <div class="mt-10">
              <h3 class="text-lg font-medium text-highlighted">
                {{ features[1].title }}
              </h3>
              <p class="mt-2 text-sm text-muted">
                {{ features[1].description }}
              </p>
            </div>
          </article>

          <article
            v-for="(f, i) in features.slice(2)"
            :key="i"
            v-reveal="i * 80"
            class="lift rounded-2xl border border-default p-7 md:col-span-3 lg:col-span-2"
          >
            <UIcon :name="f.icon" class="size-6 text-primary" />
            <h3 class="mt-5 font-medium text-highlighted">
              {{ f.title }}
            </h3>
            <p class="mt-2 text-sm text-muted">
              {{ f.description }}
            </p>
          </article>
        </div>
      </UContainer>
    </section>

    <!-- 3b. PRODUCT GALLERY — real screenshots -->
    <section class="py-12 sm:py-16">
      <UContainer>
        <div v-reveal class="max-w-2xl">
          <h2 class="text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
            El panel que usan tus doctores
          </h2>
          <p class="mt-4 text-lg leading-relaxed text-muted">
            No es una maqueta. Estas son pantallas reales del sistema en producción.
          </p>
        </div>

        <div v-reveal class="mt-10">
          <!-- Tabs -->
          <div class="flex flex-wrap gap-2">
            <button
              v-for="(g, i) in gallery"
              :key="i"
              type="button"
              class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors"
              :class="galleryIndex === i
                ? 'bg-primary text-inverted'
                : 'border border-default text-muted hover:text-default'"
              @click="galleryIndex = i"
            >
              {{ g.label }}
            </button>
          </div>

          <!-- Active screenshot -->
          <div class="mt-6">
            <BrowserFrame
              :key="gallery[galleryIndex].src"
              :src="gallery[galleryIndex].src"
              :alt="`Panel de NexoSoftDev: ${gallery[galleryIndex].label}`"
            />
            <p class="mt-4 max-w-xl text-muted">
              {{ gallery[galleryIndex].caption }}
            </p>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- 4. PRODUCT SHOWCASE — calendar mock, text right -->
    <UContainer class="py-8 sm:py-12">
      <div v-reveal class="rounded-3xl bg-elevated/40 border border-default p-6 sm:p-10 lg:p-14">
        <div class="grid lg:grid-cols-2 gap-10 items-center">
          <!-- calendar mock -->
          <div v-parallax="-24" class="rounded-2xl border border-default bg-default p-5 shadow-sm">
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

    <!-- 5. HOW IT WORKS -->
    <section id="como-funciona" class="py-20 sm:py-28">
      <UContainer>
        <div v-reveal class="max-w-2xl">
          <h2 class="text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
            Empieza en tres pasos
          </h2>
          <p class="mt-4 text-lg leading-relaxed text-muted">
            De cero a recibir pacientes en línea el mismo día.
          </p>
        </div>

        <!-- Connected steps: a thin rule ties them as one sequence -->
        <ol class="mt-14 grid gap-10 md:grid-cols-3 md:gap-8">
          <li
            v-for="(s, i) in steps"
            v-reveal="i * 110"
            :key="i"
            class="relative"
          >
            <div class="flex items-center gap-4">
              <span class="flex size-10 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-primary/5 text-sm font-medium tabular-nums text-primary">
                {{ s.step }}
              </span>
              <span
                v-if="i < steps.length - 1"
                class="hidden h-px flex-1 bg-gradient-to-r from-primary/30 to-transparent md:block"
              />
            </div>
            <h3 class="mt-5 text-lg font-medium text-highlighted">
              {{ s.title }}
            </h3>
            <p class="mt-2 text-muted">
              {{ s.description }}
            </p>
          </li>
        </ol>
      </UContainer>
    </section>

    <!-- 6. USE CASES -->
    <section id="casos" class="py-8 sm:py-12">
      <UContainer>
        <div class="grid gap-4 md:grid-cols-3">
          <article
            v-for="(c, i) in useCases"
            v-reveal="i * 80"
            :key="i"
            class="lift rounded-2xl border border-default bg-elevated/30 p-7"
          >
            <UIcon :name="c.icon" class="size-7 text-primary" />
            <h3 class="mt-5 text-lg font-medium text-highlighted">
              {{ c.title }}
            </h3>
            <p class="mt-2 text-muted">
              {{ c.description }}
            </p>
          </article>
        </div>
      </UContainer>
    </section>

    <!-- 7. TESTIMONIALS -->
    <section class="py-20 sm:py-28">
      <UContainer>
        <h2 v-reveal class="max-w-2xl text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
          Doctores que ya dejaron de perseguir confirmaciones
        </h2>

        <div class="mt-12 grid gap-4 md:grid-cols-3">
          <figure
            v-for="(t, i) in testimonials"
            v-reveal="i * 80"
            :key="i"
            class="lift flex flex-col justify-between rounded-2xl border border-default p-7"
          >
            <blockquote class="text-default leading-relaxed">
              {{ t.quote }}
            </blockquote>
            <figcaption class="mt-6 flex items-center gap-3 border-t border-default pt-5">
              <span class="flex size-9 items-center justify-center rounded-full bg-primary/10">
                <UIcon name="i-lucide-user" class="size-4 text-primary" />
              </span>
              <span>
                <span class="block text-sm font-medium text-highlighted">{{ t.name }}</span>
                <span class="block text-xs text-muted">{{ t.role }}</span>
              </span>
            </figcaption>
          </figure>
        </div>
      </UContainer>
    </section>

    <!-- 8. PRICING -->
    <section id="precios" class="py-20 sm:py-28">
      <UContainer>
        <div v-reveal class="max-w-2xl">
          <h2 class="text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
            Precios claros, en pesos
          </h2>
          <p class="mt-4 text-lg leading-relaxed text-muted">
            Empieza gratis. Sube de plan cuando tu consultorio lo pida. Sin contratos forzosos.
          </p>
        </div>

        <div class="mt-12 grid gap-6 lg:grid-cols-3 items-stretch">
        <div
          v-for="(p, i) in plans"
          v-reveal="i * 90"
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
          <p class="mt-1 text-xs text-dimmed">
            Precio de referencia
          </p>
          <UButton
            class="mt-5 justify-center"
            block
            v-bind="p.button"
            @click="openLead(p.slug)"
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
      <div v-reveal class="mt-6 rounded-2xl border border-default bg-elevated/40 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
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
          @click="openLead('enterprise')"
        />
        </div>
      </UContainer>
    </section>

    <!-- 9. FINAL CTA -->
    <UPageSection>
      <UPageCTA
        title="Tu agenda en producción, no en presentación"
        description="Prueba la demo en vivo con datos de ejemplo y míralo funcionando hoy mismo. Sin tarjeta, sin instalaciones, sin sorpresas en la factura."
        variant="subtle"
        :links="[{
          label: 'Probar la demo gratis',
          to: DEMO_URL,
          target: '_blank',
          trailingIcon: 'i-lucide-arrow-right',
          size: 'xl'
        }, {
          label: 'Hablar con nosotros',
          color: 'neutral',
          variant: 'outline',
          size: 'xl',
          onSelect: () => openLead('')
        }]"
      />
    </UPageSection>
  </div>
</template>
