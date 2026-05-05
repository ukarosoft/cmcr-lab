# CMCR Lab — Contexto del Proyecto

## Cliente
- **Empresa:** Centro Clínico Madre Carmen Rendiles C.A
- **RIF:** J-501965030
- **Negocio:** Laboratorio clínico — gestión de inventario de insumos y producción de reactivos
- **Contacto:** Por definir
- **Partner:** SmartSolutions

## Stack
Heredado de ukaro-boilerplate. Django 5.x + Tailwind CDN + ukaro.css + Alpine.js + HTMX + SQLite (dev) / PostgreSQL (prod).

## Módulos implementados

### `lab_inventory` — Gestión de inventario y producción
Modelos:
- **Category** — Categorías de insumos
- **UnitOfMeasure** — Unidades de medida (kg, L, mL, unidad, etc.)
- **Supplier** — Proveedores (RIF, contacto, teléfono, email)
- **Supply** — Insumos con stock min/max, trazabilidad por lote
- **StockMovement** — Entradas, salidas, ajustes (con lote, proveedor, OP)
- **Reagent** — Reactivos con receta/BOM (instrucciones, rendimiento)
- **ReagentItem** — Ítems de receta (insumo + cantidad necesaria)
- **ProductionOrder** — Órdenes de producción (planificada → en proceso → completada → cancelada)

## Comandos
- Dev: `source env/bin/activate && DJANGO_SETTINGS_MODULE=config.settings.dev python3 manage.py runserver`
- Tests: `DJANGO_SETTINGS_MODULE=config.settings.dev pytest --tb=short`
- Shell: `source env/bin/activate && DJANGO_SETTINGS_MODULE=config.settings.dev python3 manage.py shell`
- Check: `source env/bin/activate && DJANGO_SETTINGS_MODULE=config.settings.dev python3 manage.py check`

## Credenciales dev
- Usuario: admin
- Password: admin123
- Organización: Centro Clínico Madre Carmen Rendiles (slug: cmcr)

## Repositorio
https://github.com/ukarosoft/cmcr-lab

## Pendientes
- [ ] Diseñar landing page de login con identidad CMCR
- [ ] Tests para todos los modelos y vistas
- [ ] Seed data: categorías, unidades de medida típicas de laboratorio
- [ ] Sistema de alertas por email cuando stock < mínimo
- [ ] Reportes de consumo y producción (PDF/Excel)
- [ ] Dashboard con gráficos ApexCharts
- [ ] Deploy a Render o PythonAnywhere para pruebas con el cliente
