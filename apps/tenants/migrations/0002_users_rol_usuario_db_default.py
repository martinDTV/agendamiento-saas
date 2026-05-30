"""
Give users_user.rol_usuario a DB-level default.

The django-users-auth package ships a migration that adds a NOT NULL
`rol_usuario` column, but its User model does not declare the field. So any
INSERT that doesn't explicitly set it (e.g. the demo seeder, or the auth
register flow) fails with IntegrityError on a clean database. We can't patch the
third-party package, so we set a database default on the orphan column. This is
idempotent and safe on existing databases.
"""
from django.db import migrations


SET_DEFAULT = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users_user' AND column_name = 'rol_usuario'
    ) THEN
        ALTER TABLE users_user ALTER COLUMN rol_usuario SET DEFAULT 'usuario_normal';
        UPDATE users_user SET rol_usuario = 'usuario_normal' WHERE rol_usuario IS NULL;
    END IF;
END $$;
"""

UNSET_DEFAULT = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users_user' AND column_name = 'rol_usuario'
    ) THEN
        ALTER TABLE users_user ALTER COLUMN rol_usuario DROP DEFAULT;
    END IF;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('users', '0002_user_rol_usuario'),
    ]

    operations = [
        migrations.RunSQL(SET_DEFAULT, reverse_sql=UNSET_DEFAULT),
    ]
