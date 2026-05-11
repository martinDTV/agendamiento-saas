"""
Llena el tenant `sanatorio-metropolitano` con datos realistas:
- Settings/branding
- 3 sucursales
- 14 servicios médicos
- 8 doctores (con User + Membership + Doctor)
- Horarios semanales (L-V) por doctor
- 25 citas en los próximos 14 días (mezcla de pendientes/confirmadas/completadas)

Idempotente: usa get_or_create / update_or_create.
"""
from __future__ import annotations

import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Membership, MembershipRole
from apps.bookings.models import Appointment, AppointmentStatus
from apps.catalog.models import Branch, Doctor, Schedule, Service
from apps.tenants.models import Tenant

User = get_user_model()
TENANT_SLUG = 'sanatorio-metropolitano'
DEFAULT_PASSWORD = 'S@n@torio2026!'


# ────────────────────────────── DATOS ──────────────────────────────

TENANT_SETTINGS = {
    'timezone': 'America/Mexico_City',
    'locale': 'es-MX',
    'currency': 'MXN',
    'branding': {
        'primary_color': '#0EA5E9',
        'secondary_color': '#0F766E',
        'logo_url': '',
        'tagline': 'Cuidamos tu salud con tecnología y humanidad',
    },
    'contact': {
        'phone': '+52 55 5512 8800',
        'email': 'contacto@sanatoriometropolitano.mx',
        'website': 'https://sanatoriometropolitano.mx',
    },
    'features': {
        'online_booking': True,
        'reminders_24h': True,
        'ai_suggestions': True,
    },
}

BRANCHES = [
    {
        'name': 'Sede Centro',
        'address': 'Av. Reforma 1245, Col. Cuauhtémoc, CDMX 06500',
        'phone': '+52 55 5512 8800',
    },
    {
        'name': 'Sucursal Polanco',
        'address': 'Av. Presidente Masaryk 220, Col. Polanco, CDMX 11550',
        'phone': '+52 55 5280 4410',
    },
    {
        'name': 'Sucursal Coyoacán',
        'address': 'Av. Universidad 1810, Col. Romero de Terreros, CDMX 04310',
        'phone': '+52 55 5658 2233',
    },
]

SERVICES = [
    ('Consulta de Medicina General', 'Valoración clínica integral con médico general.', 30, 600, '#3B82F6'),
    ('Consulta Pediátrica', 'Atención médica especializada para niños y adolescentes.', 30, 750, '#F59E0B'),
    ('Consulta Ginecológica', 'Revisión ginecológica y orientación reproductiva.', 40, 900, '#EC4899'),
    ('Consulta Cardiológica', 'Evaluación cardiovascular y electrocardiograma.', 45, 1500, '#EF4444'),
    ('Consulta Dermatológica', 'Diagnóstico y tratamiento de afecciones de la piel.', 30, 950, '#A855F7'),
    ('Consulta Ortopédica', 'Atención de lesiones musculoesqueléticas.', 40, 1100, '#14B8A6'),
    ('Consulta Oftalmológica', 'Examen visual completo y prescripción de lentes.', 40, 1000, '#6366F1'),
    ('Consulta Otorrinolaringología', 'Atención de oído, nariz y garganta.', 30, 950, '#0EA5E9'),
    ('Consulta Psicológica', 'Sesión terapéutica con psicólogo clínico.', 60, 850, '#8B5CF6'),
    ('Consulta Nutrición', 'Plan alimenticio y seguimiento nutricional.', 45, 700, '#22C55E'),
    ('Consulta Endocrinología', 'Tratamiento de trastornos hormonales y metabólicos.', 40, 1300, '#F97316'),
    ('Electrocardiograma', 'Estudio eléctrico del corazón en reposo.', 20, 450, '#DC2626'),
    ('Ultrasonido Abdominal', 'Estudio de imagen no invasivo de abdomen.', 30, 850, '#0891B2'),
    ('Laboratorio Clínico Básico', 'Biometría hemática y química sanguínea.', 15, 380, '#84CC16'),
]

DOCTORS = [
    # (first, last, specialty, branch_idx, duration, bio)
    ('Andrea',   'Hernández Salinas',  'Medicina General',         0, 30,
     'Médica general egresada de la UNAM con 12 años de experiencia en consulta familiar.'),
    ('Luis',     'Ramírez Ortiz',      'Pediatría',                0, 30,
     'Pediatra certificado por el CMP, especializado en desarrollo infantil y vacunación.'),
    ('Mariana',  'Flores Cárdenas',    'Ginecología y Obstetricia', 1, 40,
     'Ginecóloga obstetra con maestría en medicina materno-fetal por el INPer.'),
    ('Roberto',  'Mendoza Cabral',     'Cardiología',              0, 45,
     'Cardiólogo intervencionista, miembro de la Sociedad Mexicana de Cardiología.'),
    ('Patricia', 'Vega Domínguez',     'Dermatología',             1, 30,
     'Dermatóloga con subespecialidad en dermatoscopia y dermatología oncológica.'),
    ('Jorge',    'Espinoza Núñez',     'Ortopedia y Traumatología', 2, 40,
     'Ortopedista, especialista en cirugía de rodilla y medicina deportiva.'),
    ('Claudia',  'Reyes Beltrán',      'Oftalmología',             2, 40,
     'Oftalmóloga subespecialista en córnea y cirugía refractiva con láser.'),
    ('Daniel',   'Castro Aguilar',     'Psicología Clínica',       0, 60,
     'Psicólogo clínico con enfoque cognitivo-conductual, 10 años de práctica privada.'),
]

# Mapeo de especialidad → servicio principal (por nombre)
SPECIALTY_TO_SERVICE = {
    'Medicina General':           'Consulta de Medicina General',
    'Pediatría':                  'Consulta Pediátrica',
    'Ginecología y Obstetricia':  'Consulta Ginecológica',
    'Cardiología':                'Consulta Cardiológica',
    'Dermatología':               'Consulta Dermatológica',
    'Ortopedia y Traumatología':  'Consulta Ortopédica',
    'Oftalmología':               'Consulta Oftalmológica',
    'Psicología Clínica':         'Consulta Psicológica',
}

# Servicios extra por especialidad (además del servicio principal).
# Permite que un cardiólogo ofrezca su consulta + electrocardiograma, etc.
SPECIALTY_TO_EXTRA_SERVICES = {
    'Medicina General':           ['Laboratorio Clínico Básico'],
    'Pediatría':                  ['Laboratorio Clínico Básico'],
    'Ginecología y Obstetricia':  ['Ultrasonido Abdominal'],
    'Cardiología':                ['Electrocardiograma'],
    'Dermatología':               [],
    'Ortopedia y Traumatología':  [],
    'Oftalmología':               [],
    'Psicología Clínica':         [],
}

# Servicios "transversales" que cualquier doctor puede ofrecer (vacío en este sanatorio).
SHARED_SERVICES: list[str] = []

PATIENTS = [
    ('María Fernanda Gómez',   'maria.gomez@example.com',     '+52 55 1234 5678'),
    ('Carlos Eduardo Pérez',   'carlos.perez@example.com',    '+52 55 2345 6789'),
    ('Sofía Jiménez Rivera',   'sofia.jimenez@example.com',   '+52 55 3456 7890'),
    ('Diego Alarcón Martínez', 'diego.alarcon@example.com',   '+52 55 4567 8901'),
    ('Valentina Ortega León',  'valentina.ortega@example.com','+52 55 5678 9012'),
    ('Andrés Solís Maldonado', 'andres.solis@example.com',    '+52 55 6789 0123'),
    ('Renata Cárdenas Pinto',  'renata.cardenas@example.com', '+52 55 7890 1234'),
    ('Mateo Villanueva Ruiz',  'mateo.villanueva@example.com','+52 55 8901 2345'),
    ('Camila Núñez Estrada',   'camila.nunez@example.com',    '+52 55 9012 3456'),
    ('Sebastián Reyes Ortiz',  'sebastian.reyes@example.com', '+52 55 1122 3344'),
]


# ────────────────────────────── HELPERS ──────────────────────────────

def slot_times(start_hour: int, duration_min: int):
    """Genera un slot (start, end) que respeta la jornada del doctor."""
    start = time(start_hour, 0)
    end_minute = (start_hour * 60) + duration_min
    end = time(end_minute // 60, end_minute % 60)
    return start, end


# ────────────────────────────── SEED ──────────────────────────────

@transaction.atomic
def run():
    rng = random.Random(42)  # determinístico
    tenant = Tenant.objects.get(slug=TENANT_SLUG)
    print(f'\n=== Llenando tenant: {tenant.name} ({tenant.slug}) ===')

    # 1. SETTINGS
    tenant.settings = TENANT_SETTINGS
    tenant.save(update_fields=['settings'])
    print('✓ Settings/branding aplicados')

    # 2. BRANCHES
    branches: list[Branch] = []
    for b in BRANCHES:
        obj, created = Branch._all.update_or_create(
            tenant=tenant, name=b['name'],
            defaults={'address': b['address'], 'phone': b['phone'], 'is_active': True},
        )
        branches.append(obj)
        print(f'  {"+" if created else "·"} Sucursal: {obj.name}')

    # 3. SERVICES
    services_by_name: dict[str, Service] = {}
    for name, desc, dur, price, color in SERVICES:
        obj, created = Service._all.update_or_create(
            tenant=tenant, name=name,
            defaults={
                'description': desc,
                'duration': dur,
                'price': Decimal(price),
                'color': color,
                'is_active': True,
            },
        )
        services_by_name[name] = obj
        print(f'  {"+" if created else "·"} Servicio: {obj.name} (${obj.price})')

    # 4. DOCTORS (User + Membership + Doctor)
    doctors_created: list[Doctor] = []
    for first, last, specialty, branch_idx, dur, bio in DOCTORS:
        normalized = (first + '.' + last.split()[0]).lower().replace('á', 'a').replace('é', 'e') \
            .replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        email = f'{normalized}@sanatoriometropolitano.mx'

        user, u_created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first,
                'last_name': last,
                'is_active': True,
            },
        )
        if u_created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()

        Membership._all.update_or_create(
            tenant=tenant, user=user,
            defaults={'role': MembershipRole.DOCTOR, 'is_active': True},
        )

        doc, d_created = Doctor._all.update_or_create(
            tenant=tenant, user=user,
            defaults={
                'branch': branches[branch_idx],
                'specialty': specialty,
                'bio': bio,
                'appointment_duration': dur,
                'is_active': True,
            },
        )
        doctors_created.append(doc)

        # Vincular servicios al doctor (M2M Service.doctors)
        service_names: list[str] = []
        principal = SPECIALTY_TO_SERVICE.get(specialty)
        if principal:
            service_names.append(principal)
        service_names.extend(SPECIALTY_TO_EXTRA_SERVICES.get(specialty, []))
        service_names.extend(SHARED_SERVICES)
        for sname in service_names:
            svc = services_by_name.get(sname)
            if svc:
                svc.doctors.add(doc)

        print(f'  {"+" if d_created else "·"} Doctor: Dr. {first} {last} — {specialty} '
              f'(servicios: {", ".join(service_names) or "—"})')

    # 5. SCHEDULES (L-V mañana 08-13 y tarde 15-19)
    morning_start, morning_end = time(8, 0),  time(13, 0)
    evening_start, evening_end = time(15, 0), time(19, 0)
    for doc in doctors_created:
        for weekday in range(0, 5):  # L-V
            # Reemplaza el horario por uno solo (o lo dividimos en dos schedules si el modelo lo permite).
            # El constraint es (tenant, doctor, weekday) único → una sola fila por día.
            # Usamos la jornada completa 08:00-19:00 para no romper el constraint y dejamos
            # que el sistema de slots filtre por duración.
            Schedule._all.update_or_create(
                tenant=tenant, doctor=doc, weekday=weekday,
                defaults={'start_time': time(8, 0), 'end_time': time(19, 0), 'is_active': True},
            )
    print(f'✓ Horarios L-V 08:00-19:00 para {len(doctors_created)} doctores')

    # 6. APPOINTMENTS (próximos 14 días, sólo días hábiles)
    today = timezone.localdate()
    created_appts = 0
    used_slots: set[tuple[int, str, str]] = set()  # (doctor_id, date_iso, start_iso)
    statuses_pool = (
        [AppointmentStatus.PENDING] * 3
        + [AppointmentStatus.CONFIRMED] * 4
        + [AppointmentStatus.COMPLETED] * 2
        + [AppointmentStatus.CANCELLED] * 1
    )
    target_total = 25
    attempts = 0
    while created_appts < target_total and attempts < 500:
        attempts += 1
        doc = rng.choice(doctors_created)
        # Servicio acorde a la especialidad, fallback a Medicina General
        service_name = SPECIALTY_TO_SERVICE.get(doc.specialty, 'Consulta de Medicina General')
        service = services_by_name[service_name]

        days_offset = rng.randint(-3, 14)  # incluye algunos pasados → completed/cancelled
        appt_date = today + timedelta(days=days_offset)
        if appt_date.weekday() >= 5:  # sábado/domingo
            continue

        hour = rng.choice([8, 9, 10, 11, 12, 15, 16, 17, 18])
        minute = rng.choice([0, 30])
        start = time(hour, minute)
        end_minute = hour * 60 + minute + service.duration
        if end_minute > 19 * 60:
            continue
        end = time(end_minute // 60, end_minute % 60)

        key = (doc.pk, appt_date.isoformat(), start.isoformat())
        if key in used_slots:
            continue
        used_slots.add(key)

        patient = rng.choice(PATIENTS)
        # Status coherente con la fecha
        if days_offset < 0:
            status = rng.choice([AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED])
        else:
            status = rng.choice(statuses_pool)

        appt, created = Appointment._all.get_or_create(
            tenant=tenant, doctor=doc, date=appt_date, start_time=start,
            defaults={
                'service': service,
                'patient_name': patient[0],
                'patient_email': patient[1],
                'patient_phone': patient[2],
                'end_time': end,
                'status': status,
                'notes': '',
            },
        )
        if created:
            created_appts += 1
    print(f'✓ Citas creadas: {created_appts}')

    # ────────── RESUMEN ──────────
    print('\n=== RESUMEN ===')
    print(f'Branches:     {Branch._all.filter(tenant=tenant).count()}')
    print(f'Services:     {Service._all.filter(tenant=tenant).count()}')
    print(f'Doctors:      {Doctor._all.filter(tenant=tenant).count()}')
    print(f'Schedules:    {Schedule._all.filter(tenant=tenant).count()}')
    print(f'Memberships:  {Membership._all.filter(tenant=tenant).count()}')
    print(f'Appointments: {Appointment._all.filter(tenant=tenant).count()}')
    print(f'\nLogin doctor de prueba:  andrea.hernandez@sanatoriometropolitano.mx / {DEFAULT_PASSWORD}')


if __name__ == '__main__':
    run()
