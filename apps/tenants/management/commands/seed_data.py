"""
Management command to seed fake data for local development.

Usage:
    python manage.py seed_data                  # seed clinica-a (default)
    python manage.py seed_data --tenant drlopez # seed a specific tenant slug
    python manage.py seed_data --flush          # delete all data first, then seed
"""

import random
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Membership, MembershipRole
from apps.bookings.models import Appointment, AppointmentStatus
from apps.catalog.models import Branch, Doctor, Schedule, Service
from apps.tenants.models import Tenant

User = get_user_model()

# ── Data pools ───────────────────────────────────────────────────────────────

DOCTORS = [
    {
        "first_name": "Sofía",
        "last_name": "Ramírez Torres",
        "email": "sofia.ramirez@clinica-a.com",
        "specialty": "Medicina General",
        "bio": "Médico general con más de 10 años de experiencia en atención primaria y medicina preventiva.",
        "duration": 30,
    },
    {
        "first_name": "Andrés",
        "last_name": "López Mendoza",
        "email": "andres.lopez@clinica-a.com",
        "specialty": "Pediatría",
        "bio": "Especialista en pediatría con formación en el Hospital Infantil de México. Atención cálida y profesional.",
        "duration": 30,
    },
    {
        "first_name": "Valentina",
        "last_name": "Cruz Herrera",
        "email": "valentina.cruz@clinica-a.com",
        "specialty": "Ginecología y Obstetricia",
        "bio": "Ginecóloga certificada por el Consejo Mexicano de Ginecología. Salud reproductiva y embarazo de alto riesgo.",
        "duration": 45,
    },
    {
        "first_name": "Miguel",
        "last_name": "Fernández Soto",
        "email": "miguel.fernandez@clinica-a.com",
        "specialty": "Cardiología",
        "bio": "Cardiólogo clínico con subespecialidad en ecocardiografía. Manejo integral de enfermedades cardiovasculares.",
        "duration": 40,
    },
]

SERVICES = [
    {
        "name": "Consulta General",
        "description": "Valoración médica completa, revisión de signos vitales, diagnóstico y prescripción.",
        "duration": 30,
        "price": "450.00",
        "color": "#5B7C6B",
    },
    {
        "name": "Consulta Pediátrica",
        "description": "Atención especializada para bebés, niños y adolescentes. Incluye valoración del desarrollo.",
        "duration": 30,
        "price": "500.00",
        "color": "#7da096",
    },
    {
        "name": "Consulta Ginecológica",
        "description": "Revisión ginecológica, Papanicolaou, ultrasonido pélvico y orientación en salud reproductiva.",
        "duration": 45,
        "price": "650.00",
        "color": "#9dbfaa",
    },
    {
        "name": "Electrocardiograma",
        "description": "Estudio eléctrico del corazón para detectar arritmias, isquemia y otras alteraciones cardíacas.",
        "duration": 20,
        "price": "350.00",
        "color": "#4A6957",
    },
    {
        "name": "Consulta Cardiológica",
        "description": "Evaluación cardiovascular completa con historia clínica, exploración física y lectura de estudios.",
        "duration": 40,
        "price": "800.00",
        "color": "#3b5444",
    },
    {
        "name": "Ultrasonido Abdominal",
        "description": "Imagen diagnóstica de órganos abdominales: hígado, vesícula, riñones, páncreas y bazo.",
        "duration": 30,
        "price": "550.00",
        "color": "#73a288",
    },
    {
        "name": "Toma de Muestras de Laboratorio",
        "description": "Extracción de sangre y otras muestras. Resultados disponibles en 24–48 horas.",
        "duration": 15,
        "price": "150.00",
        "color": "#c5d6c9",
    },
    {
        "name": "Vacunación",
        "description": "Aplicación de vacunas del esquema nacional y de viajero. Incluye registro en cartilla.",
        "duration": 15,
        "price": "200.00",
        "color": "#a3c0b3",
    },
]

BRANCHES = [
    {
        "name": "Clínica Central",
        "address": "Av. Insurgentes Sur 1234, Col. Del Valle, CDMX",
        "phone": "+52 55 5555-0101",
    },
    {
        "name": "Sucursal Polanco",
        "address": "Av. Presidente Masaryk 88, Polanco, CDMX",
        "phone": "+52 55 5555-0202",
    },
]

PATIENTS = [
    ("María Elena González Ruiz", "maria.gonzalez@gmail.com", "+52 55 1111-0001"),
    ("Roberto Sánchez Pérez", "roberto.sanchez@outlook.com", "+52 55 1111-0002"),
    ("Ana Laura Martínez Jiménez", "ana.martinez@gmail.com", "+52 55 1111-0003"),
    ("Carlos Alberto Flores Morales", "carlos.flores@hotmail.com", "+52 55 1111-0004"),
    ("Patricia Vega Domínguez", "patricia.vega@gmail.com", "+52 55 1111-0005"),
    ("José Luis Hernández Reyes", "jose.hernandez@gmail.com", "+52 55 1111-0006"),
    ("Lucía Torres Ávila", "lucia.torres@outlook.com", "+52 55 1111-0007"),
    ("Fernando Morales Castro", "fernando.morales@gmail.com", "+52 55 1111-0008"),
    ("Isabel Ramos Gutiérrez", "isabel.ramos@hotmail.com", "+52 55 1111-0009"),
    ("Diego Vargas Méndez", "diego.vargas@gmail.com", "+52 55 1111-0010"),
    ("Claudia Ortiz Salinas", "claudia.ortiz@gmail.com", "+52 55 1111-0011"),
    ("Eduardo Reyes Montes", "eduardo.reyes@outlook.com", "+52 55 1111-0012"),
]

SCHEDULE_BLOCKS = [
    {"weekday": 0, "start": time(9, 0), "end": time(17, 0)},
    {"weekday": 1, "start": time(9, 0), "end": time(17, 0)},
    {"weekday": 2, "start": time(9, 0), "end": time(13, 0)},
    {"weekday": 3, "start": time(9, 0), "end": time(17, 0)},
    {"weekday": 4, "start": time(9, 0), "end": time(15, 0)},
]


def _gor_create(model, tenant, lookup, defaults=None):
    """get_or_create scoped to a tenant using _all (the unscoped manager)."""
    defaults = defaults or {}
    params = {"tenant": tenant, **lookup}
    try:
        obj = model._all.get(**params)
        return obj, False
    except model.DoesNotExist:
        obj = model._all.create(**params, **defaults)
        return obj, True


class Command(BaseCommand):
    help = "Seed fake data for local development"

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="clinica-a", help="Tenant slug (default: clinica-a)")
        parser.add_argument("--flush", action="store_true", help="Delete tenant data before seeding")

    def handle(self, *args, **options):
        slug = options["tenant"]
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n🌱  Seeding data for tenant: {slug}\n"))

        # ── Tenant ──────────────────────────────────────────────────────────
        tenant, created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={
                "name": "Clínica A",
                "type": "clinic",
                "plan": "pro",
                "is_active": True,
                "settings": {
                    "branding": {"primaryColor": "#5B7C6B", "logoUrl": None, "fontFamily": "Inter"},
                    "timezone": "America/Mexico_City",
                    "locale": "es-MX",
                },
            },
        )
        self.stdout.write(f"  {'✔' if created else '·'}  Tenant: {tenant}")

        if options["flush"]:
            self._flush(tenant)

        # ── Admin user ──────────────────────────────────────────────────────
        admin_user = self._upsert_user(
            email="admin@clinica-a.com",
            first_name="Admin",
            last_name="Clínica A",
            password="Cl1n1c@Secure2024!",
        )
        _gor_create(Membership, tenant, {"user": admin_user}, {"role": MembershipRole.OWNER})
        self.stdout.write("  ✔  Admin user listo")

        # ── Branches ────────────────────────────────────────────────────────
        branches = []
        for b in BRANCHES:
            branch, created = _gor_create(
                Branch, tenant, {"name": b["name"]},
                {"address": b["address"], "phone": b["phone"], "is_active": True},
            )
            branches.append(branch)
            self.stdout.write(f"  {'✔' if created else '·'}  Sucursal: {branch.name}")

        # ── Doctors ─────────────────────────────────────────────────────────
        doctor_objects = []
        for i, d in enumerate(DOCTORS):
            user = self._upsert_user(
                email=d["email"],
                first_name=d["first_name"],
                last_name=d["last_name"],
                password="Doctor2024!",
            )
            doctor, created = _gor_create(
                Doctor, tenant, {"user": user},
                {
                    "specialty": d["specialty"],
                    "bio": d["bio"],
                    "appointment_duration": d["duration"],
                    "branch": branches[i % len(branches)],
                    "is_active": True,
                },
            )
            doctor_objects.append(doctor)
            _gor_create(Membership, tenant, {"user": user}, {"role": MembershipRole.DOCTOR})
            self.stdout.write(f"  {'✔' if created else '·'}  Doctor: {user.get_full_name()} ({d['specialty']})")

        # ── Schedules ───────────────────────────────────────────────────────
        n_schedules = 0
        for doctor in doctor_objects:
            blocks = SCHEDULE_BLOCKS[:]
            if doctor.appointment_duration < 40:
                blocks.append({"weekday": 5, "start": time(9, 0), "end": time(13, 0)})
            for block in blocks:
                _, created = _gor_create(
                    Schedule, tenant,
                    {"doctor": doctor, "weekday": block["weekday"]},
                    {"start_time": block["start"], "end_time": block["end"], "is_active": True},
                )
                if created:
                    n_schedules += 1
        self.stdout.write(f"  ✔  {n_schedules} bloques de horario")

        # ── Services ────────────────────────────────────────────────────────
        service_objects = []
        for s in SERVICES:
            service, created = _gor_create(
                Service, tenant, {"name": s["name"]},
                {
                    "description": s["description"],
                    "duration": s["duration"],
                    "price": s["price"],
                    "color": s["color"],
                    "is_active": True,
                },
            )
            service_objects.append(service)
            self.stdout.write(f"  {'✔' if created else '·'}  Servicio: {service.name}")

        # ── Appointments ────────────────────────────────────────────────────
        n_appts = self._seed_appointments(tenant, doctor_objects, service_objects)
        self.stdout.write(f"  ✔  {n_appts} citas generadas")

        # ── Summary ─────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n✅  Seed completado.\n"))
        self.stdout.write("  Admin panel → http://admin.clinica-a.miapp.com:3002")
        self.stdout.write("  Email:        admin@clinica-a.com")
        self.stdout.write("  Password:     Cl1n1c@Secure2024!\n")

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _upsert_user(self, email, first_name, last_name, password):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name, "username": email},
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    def _flush(self, tenant):
        self.stdout.write(self.style.WARNING("  ⚠  Borrando datos existentes del tenant…"))
        Appointment._all.filter(tenant=tenant).delete()
        Schedule._all.filter(tenant=tenant).delete()
        Doctor._all.filter(tenant=tenant).delete()
        Service._all.filter(tenant=tenant).delete()
        Branch._all.filter(tenant=tenant).delete()
        Membership._all.filter(tenant=tenant).delete()

    def _seed_appointments(self, tenant, doctors, services):
        today = date.today()
        count = 0

        past_statuses = [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.CONFIRMED,
        ]
        future_statuses = [
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.PENDING,
            AppointmentStatus.PENDING,
        ]

        def make_appt(appt_date, doctor, service, start_h, start_m, status):
            nonlocal count
            start = time(start_h, start_m)
            total_min = start_h * 60 + start_m + service.duration
            end_h = min(total_min // 60, 18)
            end_m = total_min % 60
            end = time(end_h, end_m)
            patient = random.choice(PATIENTS)
            try:
                _, created = _gor_create(
                    Appointment, tenant,
                    {"doctor": doctor, "date": appt_date, "start_time": start},
                    {
                        "service": service,
                        "patient_name": patient[0],
                        "patient_email": patient[1],
                        "patient_phone": patient[2],
                        "end_time": end,
                        "status": status,
                    },
                )
                if created:
                    count += 1
            except Exception:
                pass

        # Últimos 30 días
        for delta in range(-30, 0):
            d = today + timedelta(days=delta)
            if d.weekday() >= 6:
                continue
            for _ in range(random.randint(2, 5)):
                make_appt(d, random.choice(doctors), random.choice(services),
                          random.randint(9, 15), random.choice([0, 30]),
                          random.choice(past_statuses))

        # Hoy
        for i in range(random.randint(4, 8)):
            h = 9 + i
            if h > 16:
                break
            status = AppointmentStatus.CONFIRMED if i < 3 else AppointmentStatus.PENDING
            make_appt(today, random.choice(doctors), random.choice(services), h, 0, status)

        # Próximos 14 días
        for delta in range(1, 15):
            d = today + timedelta(days=delta)
            if d.weekday() >= 6:
                continue
            for _ in range(random.randint(2, 6)):
                make_appt(d, random.choice(doctors), random.choice(services),
                          random.randint(9, 15), random.choice([0, 30]),
                          random.choice(future_statuses))

        return count
