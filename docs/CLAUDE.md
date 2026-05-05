# ukaro-boilerplate — Contexto para Claude Code

## Qué es este proyecto

Base reutilizable para todos los proyectos de Ukarasoft Technology.
Cada proyecto cliente se crea clonando este boilerplate y adaptando el módulo de negocio específico.

**GitHub:** `ukarosoft/ukaro-boilerplate` (privado)
**Último score de auditoría:** 92/100 (Semana 2, 2026-04-16)

## Estructura de directorios

```
ukaro-boilerplate/
├── apps/
│   ├── core/                   # Organization, User, middleware, decoradores
│   │   ├── models.py           # TenantModel, SoftDeleteModel, TenantSoftDeleteModel
│   │   ├── middleware.py       # TenantMiddleware — inyecta request.tenant
│   │   ├── decorators.py       # @role_required, @superadmin_required, @tenant_required
│   │   ├── admin.py            # Admin filtrado por org (no expone datos cross-tenant)
│   │   └── tests/              # 46 tests cubriendo models, middleware, decorators, views
│   └── notifications/          # Sistema de notificaciones in-app
├── config/
│   ├── settings/
│   │   ├── base.py             # Configuración compartida
│   │   ├── dev.py              # Debug=True, SQLite, debug-toolbar
│   │   └── prod.py             # PostgreSQL, Sentry, security headers
│   └── urls.py                 # core + notifications + healthz
├── templates/
│   ├── base.html               # Layout principal (dark mode, Alpine, HTMX, ukaro.css)
│   └── components/
│       └── _navbar.html        # Navbar con dark mode toggle (Alpine.js + localStorage)
├── static/css/ukaro.css        # v2.0 — ~100 vars CSS + dark mode + componentes
├── scripts/
│   └── backup.sh               # pg_dump con rotación 7 días
├── nginx/default.conf          # SSL, rate limits, gzip, security headers
├── Dockerfile                  # Multi-stage (builder + runtime), no-root user ukaro
├── docker-compose.yml          # web + db + nginx + certbot, resource limits
└── .github/workflows/ci.yml    # lint (ruff) + tests (pytest + postgres)
```

## Modelos del core

### Organization

```python
# apps/core/models.py
class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    plan = models.CharField(max_length=20, choices=PLANS, default='starter')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_usuarios(self):
        return self.users.filter(is_active=True).count()
```

### User

```python
class User(AbstractUser):
    ROLES = [('superadmin', ...), ('admin', ...), ('manager', ...), ('staff', ...)]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, null=True, blank=True, ...)
    role = models.CharField(max_length=20, choices=ROLES, default='staff')

    @property
    def is_superadmin(self): return self.role == 'superadmin'

    @property
    def is_admin(self): return self.role == 'admin'
```

### TenantModel (base para módulos)

```python
class TenantModel(models.Model):
    organization = models.ForeignKey('core.Organization', on_delete=models.PROTECT, ...)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = TenantManager()     # .for_tenant(org) filtra por organization

    class Meta:
        abstract = True
```

### TenantSoftDeleteModel (combinado — evita bug MRO)

```python
class TenantSoftDeleteModel(models.Model):
    organization = models.ForeignKey('core.Organization', on_delete=models.PROTECT, ...)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, ...)
    objects = TenantSoftDeleteManager()   # .for_tenant(org).active() / .deleted()
    all_objects = models.Manager()        # acceso a todos sin filtros

    class Meta:
        abstract = True
```

## TenantMiddleware

Inyecta `request.tenant` en cada request:
- Usuario anónimo → `request.tenant = None` (pasa)
- Superadmin → `request.tenant = None` (acceso total)
- Usuario sin org → redirige a `/login/`
- Org inactiva → redirige a `/cuenta-suspendida/`
- Usuario con org activa → `request.tenant = user.organization`

Rutas públicas (no verifican tenant): `/login/`, `/logout/`, `/healthz/`, `/admin/`, `/cuenta-suspendida/`

## Decoradores disponibles

```python
from apps.core.decorators import role_required, superadmin_required, tenant_required

@role_required('admin', 'manager')  # acceso solo con esos roles (superadmin siempre pasa)
@superadmin_required                # solo superadmins
@tenant_required                    # cualquier usuario autenticado con tenant activo
```

## Cómo crear un módulo nuevo

```bash
python manage.py startapp nombre_modulo apps/nombre_modulo
```

Estructura mínima de un módulo:

```python
# apps/mi_modulo/models.py
from apps.core.models import TenantModel

class MiModelo(TenantModel):
    nombre = models.CharField(max_length=150)
    # TenantModel ya incluye: organization, created_at, updated_at
    # Usar en vistas: MiModelo.objects.for_tenant(request.tenant)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'mis modelos'
```

```python
# apps/mi_modulo/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from apps.core.decorators import tenant_required

class MiModeloListView(LoginRequiredMixin, ListView):
    model = MiModelo
    template_name = 'mi_modulo/lista.html'
    context_object_name = 'objetos'

    def get_queryset(self):
        return MiModelo.objects.for_tenant(self.request.tenant)
```

## Variables de entorno

```bash
# .env (copiar desde .env.example)
SECRET_KEY=<generar con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
DEBUG=False
ALLOWED_HOSTS=midominio.com
SENTRY_DSN=          # opcional
APP_NAME=MiApp       # nombre visible en navbar
```

## Comandos de desarrollo

```bash
# Setup inicial
git clone git@github.com:ukarosoft/ukaro-boilerplate.git mi-proyecto
cd mi-proyecto
python3 -m venv env && source env/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser

# Tests
DJANGO_SETTINGS_MODULE=config.settings.dev python -m pytest apps/core/tests/ -v

# Coverage
DJANGO_SETTINGS_MODULE=config.settings.dev python -m pytest --cov=apps --cov-report=term-missing

# Linting
ruff check . && ruff format --check .
```

## Deploy con Docker

```bash
# Producción
cp .env.example .env && vim .env  # configurar variables reales
docker compose up -d db
docker compose up -d web nginx

# Con SSL (después de apuntar dominio)
docker compose --profile certbot run certbot

# Backup manual
./scripts/backup.sh

# Cron backup (2am diario) — agregar con: crontab -e
0 2 * * * cd /opt/app && bash scripts/backup.sh >> /var/log/backup.log 2>&1
```

## CI/CD

GitHub Actions en `.github/workflows/ci.yml`:
- `lint`: ruff check + ruff format
- `test`: pytest con PostgreSQL en Docker, coverage report

Los tests corren automáticamente en cada push a `main` y en PRs.

## Convenciones Ukarasoft

- Código en inglés, comentarios y docs en español
- CBV para CRUD, FBV para endpoints HTMX
- Fat models: lógica en modelos o `services.py`, no en vistas
- Templates: partials prefijados con `_` (ej: `_form.html`, `_tabla.html`)
- NUNCA queries sin `.for_tenant()` en vistas normales
- NUNCA colores hardcodeados — variables CSS de `ukaro.css`
- NUNCA JS inline — Alpine.js al final del template

## Tests — patrón estándar

```python
# conftest.py (ya configurado en el boilerplate)
# Fixtures disponibles: org_a, org_b, admin_user, superadmin_user, auth_client, rf, client

class TestMiVistaList:
    def test_lista_solo_tenant(self, auth_client, org_a, org_b):
        MiModeloFactory(organization=org_a)
        MiModeloFactory(organization=org_b)  # no debe aparecer
        response = auth_client.get(reverse('mi_modulo:lista'))
        assert response.status_code == 200
        assert len(response.context['objetos']) == 1

    def test_requiere_login(self, client):
        response = client.get(reverse('mi_modulo:lista'))
        assert response.status_code == 302
        assert '/login/' in response.url
```
