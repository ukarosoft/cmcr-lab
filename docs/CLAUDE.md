# CMCR Lab — Contexto del Proyecto

## Cliente
- **Empresa:** Centro Clínico Madre Carmen Rendiles C.A
- **RIF:** J-501965030
- **Negocio:** Laboratorio clínico — gestión de inventario de insumos y producción de reactivos
- **Contacto:** Por definir
- **Partner:** SmartSolutions

## Stack
Heredado de ukaro-boilerplate. Django 6.0.5 + Tailwind CDN + ukaro.css + Alpine.js + HTMX + SQLite (dev) / PostgreSQL (prod).

## Módulos implementados

### `lab_inventory` — Gestión de inventario y producción
Modelos:
- **Category** (TenantModel) — Categorías de insumos
- **UnitOfMeasure** (TenantModel) — Unidades de medida (kg, L, mL, unidad, etc.)
- **Supplier** (TenantModel) — Proveedores (RIF, contacto, teléfono, email)
- **Supply** (TenantSoftDeleteModel) — Insumos con stock min/max, trazabilidad por lote
- **StockMovement** (TenantModel) — Entradas, salidas, ajustes (con lote, proveedor, OP)
- **Reagent** (TenantSoftDeleteModel) — Reactivos con receta/BOM (instrucciones, rendimiento)
- **ReagentItem** (TenantModel) — Ítems de receta (insumo + cantidad necesaria)
- **ProductionOrder** (TenantModel) — Órdenes de producción (planificada → en proceso → completada → cancelada)

### `notifications` — Notificaciones internas
- **Notification** (TenantModel) — Con índices (user, leida) y (org, -created_at)

## Reglas multi-tenant OBLIGATORIAS
1. TODO modelo hereda TenantModel o TenantSoftDeleteModel
2. TODA vista usa .for_tenant(request.tenant) en get_queryset()
3. TODA FBV usa get_object_or_404(Model.objects.for_tenant(request.tenant), ...)
4. TODO CreateView asigna form.instance.organization = request.tenant
5. TODO formulario con FK filtra opciones por tenant
6. Admin usa TenantAdminMixin con get_queryset() y save_model()
7. Management commands reciben --org-slug (NUNCA Organization.objects.first())
8. Cancelaciones crean movimientos compensatorios (NUNCA DELETE)

## Comandos
- Dev: `source env/bin/activate && python manage.py runserver`
- Tests: `pytest --tb=short`
- Seed: `python manage.py seed_demo --org-slug=cmcr`
- Shell: `python manage.py shell`
- Check: `python manage.py check`
- Check deploy: `python manage.py check --deploy`

## Credenciales dev
- Usuario: admin
- Password: admin123
- Organización: Centro Clínico Madre Carmen Rendiles (slug: cmcr)

## Repositorio
https://github.com/ukarosoft/cmcr-lab

## Estado (2026-05-05)
- 110 tests passing, 0 failing
- Auditoría multi-tenant completada — 7 fixes críticos aplicados
- Frontend: inline JS eliminado, colores via variables CSS, sidebar con active state

## Pendientes para producción
- [ ] Tests de vistas CRUD (~50 tests)
- [ ] Tests de formularios (~30 tests)
- [ ] Tests de notifications (~15 tests)
- [ ] Sistema de alertas por email cuando stock < mínimo
- [ ] Reportes de consumo y producción (PDF/Excel)
- [ ] Dashboard con gráficos ApexCharts
- [ ] Compilar Tailwind para producción
- [ ] Deploy a DigitalOcean (producción)
