<script setup lang="ts">
definePageMeta({ middleware: 'tenant' })

const tenant = useTenantStore()
const { content } = useContent()
</script>

<template>
  <div>
    <!-- ── PAGE HERO ── -->
    <section class="relative overflow-hidden pt-16 pb-12 px-6">
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-0 right-1/4 w-96 h-96 rounded-full opacity-20 blur-3xl bg-sage-100" />
      </div>
      <div class="max-w-7xl mx-auto relative text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4 bg-sage-100 text-sage-600">
          <UIcon name="i-lucide-mail" class="w-3.5 h-3.5" />
          {{ content.nav.contacto }}
        </div>
        <h1 class="text-4xl font-bold tracking-tight mb-3 text-ink">
          ¿Necesitas ayuda?
        </h1>
        <p class="text-base text-ink-soft max-w-2xl mx-auto">
          Estamos aquí para responder tus preguntas. Agenda tu cita en línea o contáctanos directamente.
        </p>
      </div>
    </section>

    <!-- ── CONTACT INFO + CTA ── -->
    <section class="pb-20 px-6">
      <div class="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Info de la clínica -->
        <div class="bg-white rounded-2xl p-8 border border-border shadow-sm">
          <h2 class="font-semibold text-lg mb-5 text-ink">
            {{ tenant.tenant?.name }}
          </h2>

          <div class="space-y-4">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-sage-100">
                <UIcon name="i-lucide-clock" class="w-4 h-4 text-sage-600" />
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Horario</p>
                <p class="text-sm text-ink">Lunes a Viernes · 9:00 - 19:00</p>
                <p class="text-sm text-ink-soft">Sábados · 9:00 - 14:00</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-sage-100">
                <UIcon name="i-lucide-calendar-check" class="w-4 h-4 text-sage-600" />
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Citas</p>
                <p class="text-sm text-ink">Disponibles 24/7 en línea</p>
                <p class="text-sm text-ink-soft">Confirmación inmediata por correo</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-sage-100">
                <UIcon name="i-lucide-shield-check" class="w-4 h-4 text-sage-600" />
              </div>
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Privacidad</p>
                <p class="text-sm text-ink-soft">
                  Tus datos están protegidos conforme a la LFPDPPP.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- CTA principal -->
        <div class="bg-sage-50 rounded-2xl p-8 border border-sage-200 flex flex-col">
          <div class="flex-1">
            <div class="inline-flex w-12 h-12 rounded-xl items-center justify-center mb-5 bg-sage-500">
              <UIcon name="i-lucide-calendar-plus" class="w-6 h-6 text-white" />
            </div>
            <h2 class="font-semibold text-lg mb-2 text-ink">
              Agenda tu cita en línea
            </h2>
            <p class="text-sm text-ink-soft mb-6">
              La forma más rápida de reservar. Elige el servicio, doctor, fecha y hora. Sin llamadas, sin esperas.
            </p>
          </div>
          <NuxtLink
            to="/agendar"
            class="inline-flex items-center justify-center gap-2 text-white font-medium px-6 py-3 rounded-xl text-sm transition-all shadow-sm bg-sage-500 hover:bg-sage-600"
          >
            <UIcon name="i-lucide-calendar-plus" class="w-4 h-4" />
            {{ content.nav.ctaLabel }}
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
