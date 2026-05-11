from django.db import migrations


PLANS = [
    {
        'slug': 'starter',
        'defaults': {
            'name': 'Starter',
            'description': 'Para clínicas pequeñas que ya empezaron a crecer.',
            'price_monthly': 299,
            'price_yearly': 2990,
            'currency': 'MXN',
            'max_doctors': 5,
            'max_appointments_per_month': 500,
            'max_branches': 3,
            'features': [
                '3 sucursales',
                '5 doctores',
                '500 citas/mes',
                'Recordatorios por SMS',
                'Soporte por email',
            ],
            'is_active': True,
            'is_public': True,
            'sort_order': 1,
        },
    },
    {
        'slug': 'pro',
        'defaults': {
            'name': 'Pro',
            'description': 'Operación sin límites. Para clínicas establecidas con varias sedes.',
            'price_monthly': 799,
            'price_yearly': 7990,
            'currency': 'MXN',
            'max_doctors': 0,  # 0 = ilimitado (convención del modelo)
            'max_appointments_per_month': 0,
            'max_branches': 0,
            'features': [
                'Sucursales ilimitadas',
                'Doctores ilimitados',
                'Citas ilimitadas',
                'Reportes avanzados',
                'Acceso a API',
                'Soporte prioritario',
            ],
            'is_active': True,
            'is_public': True,
            'sort_order': 2,
        },
    },
    {
        'slug': 'enterprise',
        'defaults': {
            'name': 'Enterprise',
            'description': 'A medida. Hablamos contigo y armamos la solución.',
            'price_monthly': 0,  # precio "Consultar" — UI lo detecta y muestra texto
            'price_yearly': 0,
            'currency': 'MXN',
            'max_doctors': 0,
            'max_appointments_per_month': 0,
            'max_branches': 0,
            'features': [
                'Todo lo de Pro',
                'SLA dedicado',
                'Onboarding personalizado',
                'Integraciones a medida',
                'Account manager',
                'SSO / SAML',
            ],
            'is_active': True,
            'is_public': True,
            'sort_order': 3,
        },
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    for entry in PLANS:
        Plan.objects.update_or_create(slug=entry['slug'], defaults=entry['defaults'])


def remove_plans(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    slugs = [p['slug'] for p in PLANS]
    Plan.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0004_backfill_subscriptions'),
    ]

    operations = [
        migrations.RunPython(seed_plans, remove_plans),
    ]
