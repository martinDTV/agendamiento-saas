from django.db import migrations, models


def create_default_settings(apps, schema_editor):
    PlatformSettings = apps.get_model('platform', 'PlatformSettings')
    PlatformSettings.objects.get_or_create(pk=1)


def delete_default_settings(apps, schema_editor):
    PlatformSettings = apps.get_model('platform', 'PlatformSettings')
    PlatformSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0002_seed_free_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_color', models.CharField(default='#6366f1', help_text='Color principal del panel (#RRGGBB)', max_length=9)),
                ('platform_name', models.CharField(default='Plataforma', max_length=100)),
                ('support_email', models.EmailField(blank=True, default='', max_length=254)),
                ('logo_url', models.URLField(blank=True, default='')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Ajustes de plataforma',
                'verbose_name_plural': 'Ajustes de plataforma',
                'db_table': 'platform_settings',
            },
        ),
        migrations.RunPython(create_default_settings, delete_default_settings),
    ]
