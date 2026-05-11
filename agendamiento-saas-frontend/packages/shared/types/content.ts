/**
 * Editable site copy stored in tenant.settings.content.
 * All fields are optional at the storage level — public site falls back to
 * DEFAULT_CONTENT when a value is missing. Admin form pre-fills with defaults.
 */

export interface IconText {
  icon: string
  text: string
}

export interface IconTitleDesc {
  icon: string
  title: string
  desc: string
}

export interface HomepageContent {
  hero: {
    badge: string
    titleLine1: string
    titleLine2: string
    description: string
    ctaPrimary: string
    ctaSecondary: string
    trustBadges: IconText[]
  }
  howItWorks: {
    title: string
    subtitle: string
    steps: IconTitleDesc[]
  }
  services: {
    title: string
    subtitle: string
    seeAllLabel: string
    emptyText: string
  }
  team: {
    title: string
    subtitle: string
    bookButtonLabel: string
  }
  finalCta: {
    title: string
    description: string
    buttonText: string
  }
}

export interface BookingContent {
  pageTitle: string
  pageSubtitle: string
  stepLabels: [string, string, string]
  step1: {
    doctorTitle: string
    reasonTitle: string
    reasonOptionalLabel: string
    reasonPlaceholder: string
    reasonButton: string
    serviceTitle: string
    suggestedBadge: string
    dateTitle: string
    slotsTitle: string
    slotsEmpty: string
    continueButton: string
  }
  step2: {
    summaryTitle: string
    formTitle: string
    nameLabel: string
    namePlaceholder: string
    emailLabel: string
    emailPlaceholder: string
    phoneLabel: string
    phonePlaceholder: string
    privacyText: string
    privacyLinkLabel: string
    privacyTextSuffix: string
    backButton: string
    confirmButton: string
    confirmingButton: string
  }
  step3: {
    successTitle: string
    successMessagePrefix: string
    bookAnotherButton: string
  }
}

export interface FooterContent {
  tagline: string
  clinicaSectionTitle: string
  legalSectionTitle: string
  legalLinks: { label: string; href: string }[]
  poweredBy: string
}

export interface NavContent {
  inicio: string
  servicios: string
  equipo: string
  contacto: string
  ctaLabel: string
}

export interface SiteContent {
  homepage: HomepageContent
  booking: BookingContent
  footer: FooterContent
  nav: NavContent
}

export const DEFAULT_CONTENT: SiteContent = {
  nav: {
    inicio: 'Inicio',
    servicios: 'Servicios',
    equipo: 'Equipo',
    contacto: 'Contacto',
    ctaLabel: 'Agendar cita',
  },
  homepage: {
    hero: {
      badge: 'Agenda tu cita en línea, 24/7',
      titleLine1: 'Tu salud,',
      titleLine2: 'a un clic de distancia',
      description: 'Agenda tu consulta de forma rápida y sencilla. Sin llamadas, sin esperas. Confirmación inmediata.',
      ctaPrimary: 'Agendar cita',
      ctaSecondary: 'Ver servicios',
      trustBadges: [
        { icon: 'i-lucide-shield-check', text: 'Datos protegidos' },
        { icon: 'i-lucide-clock', text: 'Confirmación inmediata' },
        { icon: 'i-lucide-mail', text: 'Recordatorio por correo' },
      ],
    },
    howItWorks: {
      title: '¿Cómo funciona?',
      subtitle: 'Agendar tu cita toma menos de 3 minutos',
      steps: [
        { icon: 'i-lucide-clipboard-list', title: 'Elige el servicio', desc: 'Selecciona el tipo de consulta o procedimiento que necesitas.' },
        { icon: 'i-lucide-calendar-days', title: 'Escoge fecha y hora', desc: 'Consulta la disponibilidad en tiempo real y reserva tu horario.' },
        { icon: 'i-lucide-check-circle-2', title: 'Recibe confirmación', desc: 'Te enviamos un correo de confirmación con todos los detalles.' },
      ],
    },
    services: {
      title: 'Nuestros servicios',
      subtitle: 'Atención especializada para cada necesidad',
      seeAllLabel: 'Ver todos',
      emptyText: 'Servicios disponibles próximamente',
    },
    team: {
      title: 'Nuestro equipo',
      subtitle: 'Profesionales certificados a tu servicio',
      bookButtonLabel: 'Agendar',
    },
    finalCta: {
      title: '¿Listo para agendar tu cita?',
      description: 'Elige el servicio, selecciona tu horario y recibe confirmación instantánea. Sin complicaciones.',
      buttonText: 'Agendar ahora',
    },
  },
  booking: {
    pageTitle: 'Agendar cita',
    pageSubtitle: 'Completa los pasos para reservar tu consulta',
    stepLabels: ['Selección', 'Tus datos', 'Confirmación'],
    step1: {
      doctorTitle: 'Selecciona el doctor',
      reasonTitle: 'Motivo de consulta',
      reasonOptionalLabel: '(opcional)',
      reasonPlaceholder: 'Ej: dolor de cabeza frecuente',
      reasonButton: 'Sugerir',
      serviceTitle: 'Selecciona el servicio',
      suggestedBadge: 'Sugerido',
      dateTitle: 'Selecciona la fecha',
      slotsTitle: 'Horario disponible',
      slotsEmpty: 'Sin disponibilidad para esta fecha',
      continueButton: 'Continuar',
    },
    step2: {
      summaryTitle: 'Tu selección',
      formTitle: 'Tus datos de contacto',
      nameLabel: 'Nombre completo',
      namePlaceholder: 'Juan Pérez',
      emailLabel: 'Correo electrónico',
      emailPlaceholder: 'juan@correo.com',
      phoneLabel: 'Teléfono',
      phonePlaceholder: '+52 55 1234 5678',
      privacyText: 'Al confirmar aceptas nuestro',
      privacyLinkLabel: 'aviso de privacidad',
      privacyTextSuffix: 'y el tratamiento de tus datos conforme a la LFPDPPP.',
      backButton: 'Atrás',
      confirmButton: 'Confirmar cita',
      confirmingButton: 'Confirmando…',
    },
    step3: {
      successTitle: '¡Cita confirmada!',
      successMessagePrefix: 'Recibirás un correo de confirmación en',
      bookAnotherButton: 'Agendar otra cita',
    },
  },
  footer: {
    tagline: 'Atención médica profesional con la comodidad de agendar en línea.',
    clinicaSectionTitle: 'Clínica',
    legalSectionTitle: 'Legal',
    legalLinks: [
      { label: 'Aviso de privacidad', href: '#' },
      { label: 'Términos de uso', href: '#' },
    ],
    poweredBy: 'Powered by AgendaSaaS',
  },
}
