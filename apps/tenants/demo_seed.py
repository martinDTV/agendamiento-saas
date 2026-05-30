"""
Reusable tenant seeding logic.

`seed_tenant(tenant)` populates a tenant with branches, doctors, schedules,
services and a spread of appointments. Emails are derived from the tenant slug
so multiple demo clinics never collide on the global User model.

Used by:
  - apps/tenants/management/commands/seed_data.py  (local dev, fixed slug)
  - apps/tenants/middleware.py DemoTenantMiddleware (demo, auto-created tenants)
"""

import random
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model

from apps.accounts.models import Membership, MembershipRole
from apps.bookings.models import Appointment, AppointmentStatus
from apps.catalog.models import Branch, Doctor, Schedule, Service

User = get_user_model()

DOCTORS = [
    {
        "first_name": "Sofía",
        "last_name": "Ramírez Torres",
        "local": "sofia.ramirez",
        "specialty": "Medicina General",
        "bio": "Médico general con más de 10 años de experiencia en atención primaria y medicina preventiva.",
        "duration": 30,
    },
    {
        "first_name": "Andrés",
        "last_name": "López Mendoza",
        "local": "andres.lopez",
        "specialty": "Pediatría",
        "bio": "Especialista en pediatría con formación en el Hospital Infantil de México. Atención cálida y profesional.",
        "duration": 30,
    },
    {
        "first_name": "Valentina",
        "last_name": "Cruz Herrera",
        "local": "valentina.cruz",
        "specialty": "Ginecología y Obstetricia",
        "bio": "Ginecóloga certificada por el Consejo Mexicano de Ginecología. Salud reproductiva y embarazo de alto riesgo.",
        "duration": 45,
    },
    {
        "first_name": "Miguel",
        "last_name": "Fernández Soto",
        "local": "miguel.fernandez",
        "specialty": "Cardiología",
        "bio": "Cardiólogo clínico con subespecialidad en ecocardiografía. Manejo integral de enfermedades cardiovasculares.",
        "duration": 40,
    },
]

SERVICES = [
    {"name": "Consulta General", "description": "Valoración médica completa, revisión de signos vitales, diagnóstico y prescripción.", "duration": 30, "price": "450.00", "color": "#5B7C6B"},
    {"name": "Consulta Pediátrica", "description": "Atención especializada para bebés, niños y adolescentes. Incluye valoración del desarrollo.", "duration": 30, "price": "500.00", "color": "#7da096"},
    {"name": "Consulta Ginecológica", "description": "Revisión ginecológica, Papanicolaou, ultrasonido pélvico y orientación en salud reproductiva.", "duration": 45, "price": "650.00", "color": "#9dbfaa"},
    {"name": "Electrocardiograma", "description": "Estudio eléctrico del corazón para detectar arritmias, isquemia y otras alteraciones cardíacas.", "duration": 20, "price": "350.00", "color": "#4A6957"},
    {"name": "Consulta Cardiológica", "description": "Evaluación cardiovascular completa con historia clínica, exploración física y lectura de estudios.", "duration": 40, "price": "800.00", "color": "#3b5444"},
    {"name": "Ultrasonido Abdominal", "description": "Imagen diagnóstica de órganos abdominales: hígado, vesícula, riñones, páncreas y bazo.", "duration": 30, "price": "550.00", "color": "#73a288"},
    {"name": "Toma de Muestras de Laboratorio", "description": "Extracción de sangre y otras muestras. Resultados disponibles en 24–48 horas.", "duration": 15, "price": "150.00", "color": "#c5d6c9"},
    {"name": "Vacunación", "description": "Aplicación de vacunas del esquema nacional y de viajero. Incluye registro en cartilla.", "duration": 15, "price": "200.00", "color": "#a3c0b3"},
]

BRANCHES = [
    {"name": "Clínica Central", "address": "Av. Insurgentes Sur 1234, Col. Del Valle, CDMX", "phone": "+52 55 5555-0101"},
    {"name": "Sucursal Polanco", "address": "Av. Presidente Masaryk 88, Polanco, CDMX", "phone": "+52 55 5555-0202"},
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
        return model._all.get(**params), False
    except model.DoesNotExist:
        return model._all.create(**params, **defaults), True


def _upsert_user(email, first_name, last_name, password):
    # The custom User has a NOT NULL `rol_usuario` whose model-level default is
    # not enforced at the DB level, so set it explicitly to avoid IntegrityError.
    defaults = {"first_name": first_name, "last_name": last_name, "username": email}
    if any(f.name == "rol_usuario" for f in User._meta.get_fields()):
        defaults["rol_usuario"] = "usuario_normal"
    user, created = User.objects.get_or_create(email=email, defaults=defaults)
    if created:
        user.set_password(password)
        user.save()
    return user


def flush_tenant(tenant):
    """Delete all tenant-scoped data (used before a re-seed)."""
    Appointment._all.filter(tenant=tenant).delete()
    Schedule._all.filter(tenant=tenant).delete()
    Doctor._all.filter(tenant=tenant).delete()
    Service._all.filter(tenant=tenant).delete()
    Branch._all.filter(tenant=tenant).delete()
    Membership._all.filter(tenant=tenant).delete()


def seed_tenant(tenant, *, admin_email=None, admin_password="Demo2024!", log=None):
    """
    Populate `tenant` with demo data. Returns a dict summary.

    Emails are namespaced by tenant slug (e.g. admin@<slug>.demo.local) so that
    seeding many demo clinics never collides on the global User.email unique key.
    """
    log = log or (lambda msg: None)
    slug = tenant.slug
    email_domain = f"{slug}.demo.local"
    admin_email = admin_email or f"admin@{email_domain}"

    admin_user = _upsert_user(
        email=admin_email,
        first_name="Admin",
        last_name=tenant.name,
        password=admin_password,
    )
    _gor_create(Membership, tenant, {"user": admin_user}, {"role": MembershipRole.OWNER})
    log(f"  ✔  Admin: {admin_email}")

    branches = []
    for b in BRANCHES:
        branch, _ = _gor_create(
            Branch, tenant, {"name": b["name"]},
            {"address": b["address"], "phone": b["phone"], "is_active": True},
        )
        branches.append(branch)

    doctor_objects = []
    for i, d in enumerate(DOCTORS):
        user = _upsert_user(
            email=f"{d['local']}@{email_domain}",
            first_name=d["first_name"],
            last_name=d["last_name"],
            password="Demo2024!",
        )
        doctor, _ = _gor_create(
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

    for doctor in doctor_objects:
        blocks = SCHEDULE_BLOCKS[:]
        if doctor.appointment_duration < 40:
            blocks.append({"weekday": 5, "start": time(9, 0), "end": time(13, 0)})
        for block in blocks:
            _gor_create(
                Schedule, tenant,
                {"doctor": doctor, "weekday": block["weekday"]},
                {"start_time": block["start"], "end_time": block["end"], "is_active": True},
            )

    service_objects = []
    for s in SERVICES:
        service, _ = _gor_create(
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

    n_appts = _seed_appointments(tenant, doctor_objects, service_objects)
    log(f"  ✔  {n_appts} citas, {len(doctor_objects)} doctores, {len(service_objects)} servicios")

    return {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "doctors": len(doctor_objects),
        "services": len(service_objects),
        "appointments": n_appts,
    }


def _seed_appointments(tenant, doctors, services):
    today = date.today()
    count = 0

    past_statuses = [
        AppointmentStatus.COMPLETED, AppointmentStatus.COMPLETED, AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED, AppointmentStatus.CONFIRMED,
    ]
    future_statuses = [
        AppointmentStatus.CONFIRMED, AppointmentStatus.CONFIRMED,
        AppointmentStatus.PENDING, AppointmentStatus.PENDING,
    ]

    def make_appt(appt_date, doctor, service, start_h, start_m, status):
        nonlocal count
        start = time(start_h, start_m)
        total_min = start_h * 60 + start_m + service.duration
        end = time(min(total_min // 60, 18), total_min % 60)
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

    for delta in range(-30, 0):
        d = today + timedelta(days=delta)
        if d.weekday() >= 6:
            continue
        for _ in range(random.randint(2, 5)):
            make_appt(d, random.choice(doctors), random.choice(services),
                      random.randint(9, 15), random.choice([0, 30]),
                      random.choice(past_statuses))

    for i in range(random.randint(4, 8)):
        h = 9 + i
        if h > 16:
            break
        status = AppointmentStatus.CONFIRMED if i < 3 else AppointmentStatus.PENDING
        make_appt(today, random.choice(doctors), random.choice(services), h, 0, status)

    for delta in range(1, 15):
        d = today + timedelta(days=delta)
        if d.weekday() >= 6:
            continue
        for _ in range(random.randint(2, 6)):
            make_appt(d, random.choice(doctors), random.choice(services),
                      random.randint(9, 15), random.choice([0, 30]),
                      random.choice(future_statuses))

    return count
