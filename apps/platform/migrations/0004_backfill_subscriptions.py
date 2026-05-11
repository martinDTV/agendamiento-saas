from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def backfill_subscriptions(apps, schema_editor):
    """
    Para cada Tenant sin Subscription, crea una con el Plan correspondiente
    (resuelto por slug = Tenant.plan). Si no encuentra ese plan en la tabla,
    cae al plan 'free'. Si tampoco existe 'free', salta el tenant.
    """
    Tenant = apps.get_model('tenants', 'Tenant')
    Plan = apps.get_model('platform', 'Plan')
    Subscription = apps.get_model('platform', 'Subscription')

    free_plan = Plan.objects.filter(slug='free').first()
    today = timezone.now().date()
    period_end = today + timedelta(days=365 * 10)  # 10 años para planes free, ajustable después

    for tenant in Tenant.objects.all():
        if Subscription.objects.filter(tenant=tenant).exists():
            continue

        plan = Plan.objects.filter(slug=tenant.plan).first() or free_plan
        if plan is None:
            continue

        # Free plans → status='active' sin trial. Otros → trial 14 días.
        is_free = plan.price_monthly == 0
        status = 'active' if is_free else 'trial'
        trial_ends_at = None if is_free else today + timedelta(days=14)
        current_period_end = period_end if is_free else today + timedelta(days=30)

        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=status,
            billing_cycle='monthly',
            started_at=today,
            current_period_end=current_period_end,
            trial_ends_at=trial_ends_at,
            notes='Backfill automático.',
        )


def remove_backfilled(apps, schema_editor):
    Subscription = apps.get_model('platform', 'Subscription')
    Subscription.objects.filter(notes='Backfill automático.').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0003_platformsettings'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_subscriptions, remove_backfilled),
    ]
