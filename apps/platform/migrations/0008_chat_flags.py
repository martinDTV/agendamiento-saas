from django.db import migrations


CHAT_FLAGS_BY_PLAN = {
    'starter': {'chat_human_support': True},
    'pro': {'chat_human_support': True, 'chat_ai_support': True},
    'enterprise': {'chat_human_support': True, 'chat_ai_support': True},
}


def apply_chat_flags(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    for slug, flags in CHAT_FLAGS_BY_PLAN.items():
        plan = Plan.objects.filter(slug=slug).first()
        if not plan:
            continue
        existing = plan.flags or {}
        existing.update(flags)
        plan.flags = existing
        plan.save(update_fields=['flags'])


def remove_chat_flags(apps, schema_editor):
    Plan = apps.get_model('platform', 'Plan')
    for plan in Plan.objects.all():
        flags = plan.flags or {}
        flags.pop('chat_human_support', None)
        flags.pop('chat_ai_support', None)
        plan.flags = flags
        plan.save(update_fields=['flags'])


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0007_alter_platformsettings_id_paymenttransaction'),
    ]

    operations = [
        migrations.RunPython(apply_chat_flags, remove_chat_flags),
    ]
