# Demo aislada — `demo-agendamiento.nexosoftdev.com`

Stack autocontenido para correr una **demo multiclínica por subdominio**, totalmente
**aislada de producción** (BD, dominio y proceso separados).

Cada `<clinica>.demo-agendamiento.nexosoftdev.com` crea su tenant al vuelo, lo siembra
con datos de ejemplo y lo borra solo a los `DEMO_TENANT_TTL_DAYS` días.

## Cómo funciona el subdominio

No se crea un registro DNS por clínica. Hay **un wildcard** `*.demo-agendamiento`
que apunta todo al mismo droplet. El `DemoTenantMiddleware` lee el `Host`, saca el
slug y hace `get_or_create` del tenant. DNS se configura una sola vez.

```
*.demo-agendamiento.nexosoftdev.com ──► droplet ──► Caddy
                                                       ├─ /rest/*,/admin/* ─► Django (core.demo_settings)
                                                       └─ resto            ─► Nuxt (apps/public)
                                                     Django ──► Postgres demo (volumen)
```

## Piezas

| Archivo | Qué es |
|---|---|
| `Dockerfile.backend` + `entrypoint.backend.sh` | Django con `core.demo_settings`; migra al arrancar y corre Daphne. |
| `Dockerfile.frontend` | Build de `apps/public` con env del demo; sirve el SSR de Nuxt. |
| `Dockerfile.caddy` | Caddy con plugin DNS de name.com (TLS wildcard vía DNS-01). |
| `Caddyfile` | Ruteo + TLS wildcard. |
| `docker-compose.yml` | Postgres + Redis + backend + frontend + caddy + purge diario. |
| `terraform/` | Droplet en DigitalOcean + wildcard DNS en name.com. |

## Correr local (sin TLS)

La BD demo local ya existe (`agendamiento-saas-demo`). Para el backend solo:

```bash
DJANGO_SETTINGS_MODULE=core.demo_settings python manage.py runserver
# visita con Host: clinica-del-norte.demo-agendamiento.nexosoftdev.com
```

Stack completo en Docker:

```bash
cp deploy/demo/.env.example deploy/demo/.env   # y rellena los valores
docker compose -f deploy/demo/docker-compose.yml --env-file deploy/demo/.env up -d --build
```

## Desplegar en DigitalOcean

```bash
cd deploy/demo/terraform
cp terraform.tfvars.example terraform.tfvars   # rellena tokens (git-ignored)
terraform init
terraform apply
```

Terraform crea el droplet (cloud-init instala Docker, clona el repo y levanta el
compose) y los registros `A` apex + wildcard en name.com. El primer arranque tarda
unos minutos mientras compila las imágenes y Caddy emite el certificado wildcard.

## Aislamiento (lo importante)

- **BD separada**: `DEMO_DATABASE_URL` → Postgres del compose, nunca el de producción.
- **Settings separados**: `core.demo_settings` solo sobreescribe lo necesario.
- **Sin mensajes reales**: email a consola, WhatsApp/Twilio desactivados.
- **Dominio separado**: `demo-agendamiento.nexosoftdev.com`, distinto del de prod.
- **Efímero**: `purge_demo_tenants` borra clínicas vencidas a diario.
