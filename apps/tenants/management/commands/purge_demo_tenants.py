"""
Delete expired demo tenants and all their data.

A demo tenant is one created by DemoTenantMiddleware: settings['demo'] is True and
settings['demo_expires_at'] is an ISO timestamp. Once that timestamp is in the past
the tenant, its scoped data, its memberships, and its namespaced demo users are
removed so the demo database stays small.

Usage:
    python manage.py purge_demo_tenants            # delete expired demo tenants
    python manage.py purge_demo_tenants --all      # delete ALL demo tenants
    python manage.py purge_demo_tenants --dry-run  # show what would be deleted

Intended to run periodically (cron / Celery beat) against core.demo_settings.
"""

from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Membership
from apps.bookings.models import Appointment
from apps.catalog.models import Branch, Doctor, Schedule, Service
from apps.tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = "Delete expired demo tenants and their data"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Delete all demo tenants regardless of expiry")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")

    def handle(self, *args, **options):
        delete_all = options["all"]
        dry_run = options["dry_run"]
        now = timezone.now()

        demo_tenants = [t for t in Tenant.objects.all() if t.settings.get("demo")]
        expired = [t for t in demo_tenants if delete_all or self._is_expired(t, now)]

        if not expired:
            self.stdout.write("Sin tenants demo vencidos.")
            return

        for tenant in expired:
            self._purge(tenant, dry_run)

        verb = "Se borrarían" if dry_run else "Borrados"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {len(expired)} tenant(s) demo."))

    @staticmethod
    def _is_expired(tenant, now):
        raw = tenant.settings.get("demo_expires_at")
        if not raw:
            return False
        try:
            expires_at = datetime.fromisoformat(raw)
        except ValueError:
            return False
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)
        return expires_at <= now

    def _purge(self, tenant, dry_run):
        # Users created only for this demo tenant (namespaced emails).
        demo_user_ids = list(
            Membership._all.filter(tenant=tenant).values_list("user_id", flat=True)
        )
        demo_users = User.objects.filter(
            id__in=demo_user_ids, email__endswith=f"@{tenant.slug}.demo.local"
        )

        self.stdout.write(
            f"  · {tenant.slug}: "
            f"{Appointment._all.filter(tenant=tenant).count()} citas, "
            f"{Doctor._all.filter(tenant=tenant).count()} doctores, "
            f"{demo_users.count()} usuarios"
        )
        if dry_run:
            return

        with transaction.atomic():
            Appointment._all.filter(tenant=tenant).delete()
            Schedule._all.filter(tenant=tenant).delete()
            Doctor._all.filter(tenant=tenant).delete()
            Service._all.filter(tenant=tenant).delete()
            Branch._all.filter(tenant=tenant).delete()
            Membership._all.filter(tenant=tenant).delete()
            demo_users.delete()
            tenant.delete()
