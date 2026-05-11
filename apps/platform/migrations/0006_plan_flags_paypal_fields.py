from django.db import migrations, models


# Flags por plan — fuente de verdad de qué incluye cada tier.
# Los keys deben estar en DEFAULT_FLAGS de feature_flags.py.
PLAN_FLAGS = {
    'free': {
        'email_reminders': True,
    },
    'starter': {
        'email_reminders': True,
        'sms_reminders': True,
        'ai_booking_suggestions': True,
        'reports_basic': True,
        'cms_editor': True,
    },
    'pro': {
        'email_reminders': True,
        'sms_reminders': True,
        'whatsapp_reminders': True,
        'ai_booking_suggestions': True,
        'ai_consult_summary': True,
        'ai_marketing_copy': True,
        'reports_basic': True,
        'reports_advanced': True,
        'cms_editor': True,
        'white_label': True,
        'custom_domain': True,
        'api_access': True,
        'priority_support': True,
    },
    'enterprise': {
        'email_reminders': True,
        'sms_reminders': True,
        'whatsapp_reminders': True,
        'ai_booking_suggestions': True,
        'ai_consult_summary': True,
        'ai_marketing_copy': True,
        'reports_basic': True,
        'reports_advanced': True,
        'cms_editor': True,
        'white_label': True,
        'custom_domain': True,
        'api_access': True,
        'outbound_webhooks': True,
        'sso_saml': True,
        'priority_support': True,
        'dedicated_sla': True,
    },
}


def apply_flags(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    for slug, flags in PLAN_FLAGS.items():
        Plan.objects.filter(slug=slug).update(flags=flags)


def reset_flags(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    Plan.objects.update(flags={})


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0005_seed_paid_plans'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='flags',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Feature flags booleanos. Schema en apps.platform.feature_flags.DEFAULT_FLAGS',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='paypal_product_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='plan',
            name='paypal_plan_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='subscription',
            name='paypal_subscription_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='subscription',
            name='paypal_plan_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AlterField(
            model_name='plan',
            name='features',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Lista de features incluidas (texto, para mostrar en UI)',
            ),
        ),
        migrations.RunPython(apply_flags, reset_flags),
    ]
