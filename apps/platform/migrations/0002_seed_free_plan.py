from django.db import migrations


def create_free_plan(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    Plan.objects.update_or_create(
        slug='free',
        defaults={
            'name': 'Gratuito',
            'description': 'Plan gratuito para arrancar. Límites bajos, ideal para probar la plataforma.',
            'price_monthly': 0,
            'price_yearly': 0,
            'currency': 'MXN',
            'max_doctors': 2,
            'max_appointments_per_month': 50,
            'max_branches': 1,
            'features': ['1 sucursal', '2 doctores', '50 citas/mes'],
            'is_active': True,
            'is_public': True,
            'sort_order': 0,
        },
    )


def delete_free_plan(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    Plan.objects.filter(slug='free').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_free_plan, delete_free_plan),
    ]
