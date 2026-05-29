#!/usr/bin/env bash
# Demo backend entrypoint: wait for Postgres, migrate the isolated demo DB, then run.
set -euo pipefail

echo "⏳  Esperando a Postgres…"
python - <<'PY'
import os, time, sys
import dj_database_url
import psycopg2

url = os.environ["DEMO_DATABASE_URL"]
cfg = dj_database_url.parse(url)
for attempt in range(60):
    try:
        psycopg2.connect(
            dbname=cfg["NAME"], user=cfg["USER"], password=cfg["PASSWORD"],
            host=cfg["HOST"], port=cfg["PORT"] or 5432,
        ).close()
        print("✅  Postgres listo")
        sys.exit(0)
    except Exception:
        time.sleep(2)
print("❌  Postgres no respondió")
sys.exit(1)
PY

echo "📦  Aplicando migraciones (demo DB)…"
python manage.py migrate --noinput

echo "🚀  Arrancando demo backend"
exec "$@"
