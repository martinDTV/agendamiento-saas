"""
Management command to seed fake data for local development.

Usage:
    python manage.py seed_data                  # seed clinica-a (default)
    python manage.py seed_data --tenant drlopez # seed a specific tenant slug
    python manage.py seed_data --flush          # delete all data first, then seed

The seeding logic itself lives in apps/tenants/demo_seed.py so it can be reused
by the demo subdomain auto-creation middleware.
"""

from django.core.management.base import BaseCommand

from apps.tenants.demo_seed import flush_tenant, seed_tenant
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Seed fake data for local development"

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="clinica-a", help="Tenant slug (default: clinica-a)")
        parser.add_argument("--flush", action="store_true", help="Delete tenant data before seeding")

    def handle(self, *args, **options):
        slug = options["tenant"]
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n🌱  Seeding data for tenant: {slug}\n"))

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
            self.stdout.write(self.style.WARNING("  ⚠  Borrando datos existentes del tenant…"))
            flush_tenant(tenant)

        summary = seed_tenant(
            tenant,
            admin_email="admin@clinica-a.com",
            admin_password="Cl1n1c@Secure2024!",
            log=lambda msg: self.stdout.write(msg),
        )

        self.stdout.write(self.style.SUCCESS("\n✅  Seed completado.\n"))
        self.stdout.write(f"  Email:    {summary['admin_email']}")
        self.stdout.write(f"  Password: {summary['admin_password']}\n")
