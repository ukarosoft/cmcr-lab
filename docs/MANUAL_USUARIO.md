# CMCR Lab — Manual de Usuario y Documentación Funcional

**Sistema de Gestión de Inventario y Producción de Reactivos**
**Cliente:** CMCR (Centro Médico de Consultas y Rehabilitación)
**Partner:** SmartSolutions
**Versión:** 1.0 — Mayo 2026

---

## Tabla de contenido

1. [Descripcion general del sistema](#1-descripcion-general-del-sistema)
2. [Roles y permisos](#2-roles-y-permisos)
3. [Modulos del sistema](#3-modulos-del-sistema)
4. [Flujos de proceso](#4-flujos-de-proceso)
5. [Casos de uso](#5-casos-de-uso)
6. [Guia operativa por pantalla](#6-guia-operativa-por-pantalla)
7. [Auditoria interna — analisis de logica y factibilidad](#7-auditoria-interna)

---

## 1. Descripcion general del sistema

CMCR Lab es un sistema web para gestionar el inventario de insumos quimicos y la produccion de reactivos en un laboratorio clinico. Permite:

- Registrar y clasificar insumos (materias primas)
- Definir recetas de reactivos (que insumos se necesitan para preparar cada reactivo)
- Controlar el stock con movimientos de entrada, salida y ajuste
- Crear ordenes de produccion que consumen insumos automaticamente
- Alertar cuando un insumo esta por debajo de su stock minimo
- Gestionar multiples organizaciones (multi-tenant) con aislamiento total de datos

### Arquitectura funcional

```
Proveedores → [Entrada de insumos] → Inventario de Insumos
                                          ↓
                                     Recetas de Reactivos
                                          ↓
                               Orden de Produccion (planificada)
                                          ↓
                               Iniciar produccion (consume stock)
                                          ↓
                               Completar produccion (reactivo listo)
```

### Acceso al sistema

- **URL:** https://cmcr-lab.onrender.com
- **Requisito:** Cuenta de usuario activa con organizacion asignada
- **Navegadores:** Chrome, Firefox, Safari, Edge (ultimas 2 versiones)
- **Dispositivos:** Desktop y movil (responsive)

---

## 2. Roles y permisos

El sistema tiene 4 roles jerarquicos. Cada rol hereda los permisos de los inferiores.

| Rol | Codigo | Puede ver | Puede crear/editar/eliminar | Puede gestionar produccion | Acceso admin Django |
|-----|--------|-----------|----------------------------|---------------------------|---------------------|
| **Super Admin** | `superadmin` | Todo (todas las organizaciones) | Si | Si | Si |
| **Administrador** | `admin` | Datos de su organizacion | Si | Si | Si (solo su org) |
| **Gerente** | `manager` | Datos de su organizacion | Si | Si | No |
| **Empleado** | `staff` | Datos de su organizacion | No (solo lectura) | No | No |

### Detalle por rol

**Super Admin:**
- Puede existir sin organizacion asignada (unico rol que puede)
- Ve datos de todas las organizaciones si tiene una asignada
- Acceso total al panel admin de Django
- Uso: personal tecnico de SmartSolutions/Ukarasoft

**Administrador:**
- Gestiona todos los datos de su organizacion
- Puede crear/editar/eliminar cualquier registro
- Puede iniciar, completar y cancelar ordenes de produccion
- Acceso al admin de Django filtrado a su organizacion
- Uso: director del laboratorio o jefe de area

**Gerente:**
- Mismas capacidades que admin en la aplicacion web
- Sin acceso al admin de Django
- Uso: supervisor de laboratorio, jefe de turno

**Empleado (Staff):**
- Solo lectura en todas las pantallas
- Puede ver dashboard, listas, detalles
- No puede crear, editar ni eliminar nada
- No puede gestionar ordenes de produccion
- Uso: tecnicos de laboratorio, personal auxiliar

### Reglas de seguridad

1. Todo usuario (excepto superadmin) DEBE tener una organizacion asignada
2. Un usuario solo ve datos de su propia organizacion (aislamiento multi-tenant)
3. Si la organizacion esta desactivada, el usuario ve una pantalla de "cuenta suspendida"
4. Los formularios de seleccion (dropdowns) solo muestran opciones de la organizacion del usuario

---

## 3. Modulos del sistema

### 3.1 Datos maestros

Son los catalogos base que alimentan al resto del sistema. Deben configurarse ANTES de operar.

#### 3.1.1 Categorias

Clasifican los insumos por tipo (ejemplo: "Reactivo base", "Solvente", "Buffer", "Acido", "Indicador").

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Nombre | Nombre de la categoria | Si |
| Descripcion | Detalle opcional | No |

- No se puede eliminar una categoria que tenga insumos asociados (proteccion referencial)
- El nombre es unico por organizacion

#### 3.1.2 Unidades de medida

Definen como se mide cada insumo y reactivo (ejemplo: "Litro (L)", "Mililitro (mL)", "Kilogramo (kg)", "Gramo (g)", "Unidad (uds)").

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Nombre | Nombre completo | Si |
| Abreviatura | Forma corta | Si |

- La abreviatura es unica por organizacion
- No se puede eliminar una unidad en uso

#### 3.1.3 Proveedores

Empresas o personas que suministran insumos al laboratorio.

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Nombre | Razon social o nombre comercial | Si |
| RIF | Registro fiscal | No |
| Persona de contacto | Nombre del contacto | No |
| Telefono | Numero de contacto | No |
| Email | Correo electronico | No |
| Direccion | Direccion fisica | No |
| Activo | Si el proveedor esta vigente | Si (default: Si) |

- Los proveedores se buscan por nombre o RIF
- Un proveedor inactivo no aparece en los dropdowns de nuevos movimientos

### 3.2 Inventario

#### 3.2.1 Insumos (Supplies)

Materias primas que se utilizan para preparar reactivos. Son el corazon del sistema de inventario.

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Codigo | Codigo interno unico (ej: INS-001) | No |
| Nombre | Nombre del insumo | Si |
| Descripcion | Detalle tecnico | No |
| Categoria | Tipo de insumo | Si |
| Unidad de medida | Como se mide | Si |
| Stock minimo | Alerta si el stock baja de este valor | No (default: 0) |
| Stock maximo | Referencia de capacidad maxima | No (default: 0) |
| Control por lote | Si requiere trazabilidad por lote | No (default: No) |
| Activo | Si el insumo esta en uso | Si (default: Si) |

**Propiedades calculadas:**
- **Stock actual:** se calcula sumando todos los movimientos (entradas - salidas + ajustes). NO es un campo que se edite manualmente.
- **Estado del stock:** `bajo` (≤ stock minimo), `ok` (normal), `alto` (≥ stock maximo)

**Detalle del insumo:** muestra ficha completa + historial de los ultimos 50 movimientos.

**Borrado logico:** al eliminar un insumo, se marca como eliminado pero no se borra de la base de datos. Los movimientos historicos se preservan.

#### 3.2.2 Movimientos de stock

Registran cada entrada, salida o ajuste de inventario. Son la base para calcular el stock actual.

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Insumo | Que insumo se mueve | Si |
| Tipo | Entrada, Salida o Ajuste | Si |
| Cantidad | Cuanto se mueve (siempre positivo en el form) | Si |
| Numero de lote | Lote del proveedor | No |
| Proveedor | Quien suministra (solo entradas) | No |
| Motivo | Razon del movimiento | No |

**Reglas de negocio:**
- **Entrada:** suma al stock (ej: compra de reactivos, donacion)
- **Salida:** resta del stock (ej: uso en preparacion, descarte). Se almacena como negativo internamente.
- **Ajuste:** puede sumar o restar (ej: conteo fisico revela diferencia). Se almacena tal cual.
- Cada movimiento registra automaticamente quien lo hizo y cuando
- Los movimientos generados por ordenes de produccion se vinculan a la orden
- Los movimientos NO se pueden editar ni eliminar (inmutables, por trazabilidad)

### 3.3 Reactivos

#### 3.3.1 Reactivos (productos finales)

Productos que el laboratorio prepara a partir de insumos. Ejemplo: "Solucion de NaOH 0.1M", "Buffer pH 7.0".

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Codigo | Codigo interno (ej: REA-001) | No |
| Nombre | Nombre del reactivo | Si |
| Descripcion | Detalle tecnico | No |
| Instrucciones de preparacion | Procedimiento paso a paso | No |
| Cantidad producida (yield) | Cuanto se obtiene por receta base | Si (default: 1) |
| Unidad de rendimiento | En que unidad se mide el resultado | Si |
| Control por lote | Si requiere trazabilidad | Si (default: Si) |
| Activo | Si esta en uso | Si (default: Si) |

**Borrado logico:** mismo comportamiento que insumos.

#### 3.3.2 Items de receta (ReagentItem)

Cada reactivo tiene una "receta" que define que insumos necesita y en que cantidad. Es una relacion muchos-a-muchos entre reactivo e insumo con cantidad.

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Insumo | Que materia prima se necesita | Si |
| Cantidad | Cuanto se necesita por receta base | Si |
| Unidad | En que unidad se mide | Si |
| Notas | Observaciones (ej: "agregar lentamente") | No |

- Un insumo solo puede aparecer una vez en la receta de un reactivo (restriccion unica)
- La cantidad es proporcional al `yield_quantity` del reactivo

**Ejemplo:**
Reactivo "Solucion NaOH 0.1M" (rendimiento: 1 L)
- NaOH solido: 4.0 g
- Agua destilada: 1000 mL

Si se produce una OP de 5 L, el sistema multiplica: NaOH 20g, Agua 5000 mL.

### 3.4 Produccion

#### 3.4.1 Ordenes de produccion

Documentan el proceso de preparar un reactivo. Tienen un ciclo de vida con 4 estados.

| Campo | Descripcion | Obligatorio |
|-------|-------------|-------------|
| Reactivo | Que se va a producir | Si |
| Numero de lote | Identificador del lote de produccion | Si |
| Cantidad | Cuanto se va a producir | Si |
| Observaciones | Notas del proceso | No |

**Campos automaticos:**
- Creado por (usuario)
- Fecha de creacion
- Fecha de inicio
- Fecha de completado/cancelacion
- Estado

### 3.5 Notificaciones

Alertas internas del sistema para cada usuario. Se muestran en la barra de navegacion.

| Campo | Descripcion |
|-------|-------------|
| Usuario | A quien va dirigida |
| Mensaje | Texto de la alerta |
| Tipo | info, success, warning, error |
| Leida | Si ya fue vista |

- Se pueden marcar como leidas individualmente o todas a la vez
- Cada usuario solo ve sus propias notificaciones
- Aisladas por organizacion

### 3.6 Dashboard

Pantalla principal tras el login. Muestra un resumen operativo:

- **KPIs:** total de insumos, total de reactivos, insumos con stock bajo, ordenes pendientes
- **Pipeline de produccion:** conteo por estado (planificada, en proceso, completada, cancelada)
- **Alertas de stock bajo:** lista de insumos por debajo de su stock minimo
- **Movimientos recientes:** ultimos 10 movimientos de inventario

---

## 4. Flujos de proceso

### 4.1 Flujo de configuracion inicial (primera vez)

```
1. Admin crea Categorias (tipos de insumos)
         ↓
2. Admin crea Unidades de medida (L, mL, kg, g, uds)
         ↓
3. Admin crea Proveedores
         ↓
4. Admin crea Insumos (materias primas)
         ↓
5. Admin registra stock inicial con Movimientos de Entrada
         ↓
6. Admin crea Reactivos y define sus Recetas
         ↓
7. Sistema listo para operar
```

### 4.2 Flujo de entrada de insumos (compra/recepcion)

```
Proveedor entrega insumos al laboratorio
         ↓
Admin/Gerente va a Movimientos > Nuevo
         ↓
Selecciona: Insumo, Tipo=Entrada, Cantidad, Proveedor, Lote
         ↓
Sistema registra el movimiento y actualiza el stock
         ↓
Dashboard refleja el nuevo stock
```

### 4.3 Flujo de produccion de reactivos (FLUJO PRINCIPAL)

Este es el proceso central del sistema:

```
                    ┌─────────────────┐
                    │  1. PLANIFICAR   │
                    │  Crear OP nueva  │
                    │  Estado: planned │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  2. VERIFICAR   │
                    │  ¿Hay stock     │
                    │  suficiente?    │
                    └───┬─────────┬───┘
                        │         │
                    SI  │         │ NO
                        │         │
               ┌────────▼──┐  ┌──▼──────────────┐
               │ 3. INICIAR │  │ Muestra errores  │
               │ Consume    │  │ de stock por     │
               │ insumos    │  │ cada item faltante│
               │ automatico │  └──────────────────┘
               │ Estado:    │
               │ in_progress│
               └─────┬──────┘
                     │
            ┌────────▼────────┐
            │ 4a. COMPLETAR   │         ┌──────────────────┐
            │ Reactivo listo  │    o    │ 4b. CANCELAR     │
            │ Estado:         │         │ Revierte consumos │
            │ completed       │         │ (entradas compen- │
            └─────────────────┘         │ satorias)         │
                                        │ Estado: cancelled │
                                        └──────────────────┘
```

**Detalle del paso 3 (Iniciar produccion):**
- El sistema calcula cuanto de cada insumo necesita segun la receta y la cantidad a producir
- Formula: `cantidad_necesaria = item.quantity * (orden.quantity / reactivo.yield_quantity)`
- Crea automaticamente un movimiento de salida por cada insumo de la receta
- Los movimientos quedan vinculados a la orden de produccion
- Cambia el estado a `in_progress` y registra la fecha de inicio

**Detalle del paso 4b (Cancelar):**
- Si la orden estaba `in_progress`, revierte los consumos creando movimientos de entrada compensatorios
- Si estaba `planned`, simplemente la marca como cancelada (no hay consumos que revertir)
- Registra la fecha de cancelacion

### 4.4 Flujo de ajuste de inventario

```
Se detecta diferencia entre stock teorico y conteo fisico
         ↓
Admin/Gerente va a Movimientos > Nuevo
         ↓
Selecciona: Insumo, Tipo=Ajuste, Cantidad (+ o -), Motivo
         ↓
Sistema ajusta el stock
```

### 4.5 Flujo de alerta de stock bajo

```
El stock de un insumo baja a ≤ stock_minimo
         ↓
Dashboard muestra la alerta en la seccion "Stock Bajo"
         ↓
Admin/Gerente decide: comprar mas o ajustar el minimo
         ↓
Registra entrada cuando llega el reabastecimiento
```

---

## 5. Casos de uso

### CU-01: Login al sistema

| | |
|---|---|
| **Actor** | Cualquier usuario registrado |
| **Precondicion** | Cuenta activa con organizacion activa |
| **Flujo** | 1. Usuario ingresa username y password → 2. Sistema valida credenciales → 3. Redirige al dashboard |
| **Flujo alterno** | Credenciales invalidas → muestra error "Usuario o contraseña incorrectos" |
| **Flujo alterno** | Organizacion suspendida → redirige a pantalla "cuenta suspendida" |

### CU-02: Registrar entrada de insumos

| | |
|---|---|
| **Actor** | Admin o Gerente |
| **Precondicion** | Insumo y proveedor deben existir en el sistema |
| **Flujo** | 1. Ir a Movimientos > Nuevo → 2. Seleccionar insumo, tipo "Entrada", cantidad, proveedor, lote → 3. Guardar → 4. Stock se actualiza automaticamente |
| **Resultado** | Stock del insumo incrementa en la cantidad registrada |

### CU-03: Crear reactivo con receta

| | |
|---|---|
| **Actor** | Admin o Gerente |
| **Precondicion** | Insumos y unidades deben existir |
| **Flujo** | 1. Ir a Reactivos > Nuevo → 2. Llenar datos basicos + instrucciones → 3. Guardar → 4. En el detalle del reactivo, agregar items de receta (insumo + cantidad + unidad) |
| **Resultado** | Reactivo disponible para ordenes de produccion |

### CU-04: Producir un reactivo (ciclo completo)

| | |
|---|---|
| **Actor** | Admin o Gerente |
| **Precondicion** | Reactivo con receta definida, stock suficiente de insumos |
| **Flujo** | 1. Ir a Ordenes > Nueva → 2. Seleccionar reactivo, lote, cantidad → 3. Guardar (estado: Planificada) → 4. Revisar detalle (muestra insumos necesarios vs stock disponible) → 5. Click "Iniciar produccion" → 6. Sistema consume insumos automaticamente (estado: En proceso) → 7. Cuando el tecnico termina, click "Completar" (estado: Completada) |
| **Flujo alterno** | Stock insuficiente → sistema muestra que insumos faltan y cuanto |
| **Flujo alterno** | Cancelar orden en proceso → sistema revierte consumos |

### CU-05: Consultar stock de un insumo

| | |
|---|---|
| **Actor** | Cualquier usuario autenticado (incluyendo staff) |
| **Flujo** | 1. Ir a Insumos → 2. Lista muestra nombre, codigo, categoria, stock actual, estado → 3. Click en un insumo → 4. Detalle muestra ficha completa + historial de movimientos |
| **Resultado** | Usuario ve stock actual y su historial |

### CU-06: Verificar alertas de stock bajo

| | |
|---|---|
| **Actor** | Cualquier usuario autenticado |
| **Flujo** | 1. Ir al Dashboard → 2. Ver KPI "Stock bajo" → 3. Ver lista de insumos por debajo del minimo |
| **Resultado** | Decision de reabastecimiento |

### CU-07: Marcar notificaciones como leidas

| | |
|---|---|
| **Actor** | Cualquier usuario autenticado |
| **Flujo** | 1. Click en icono de notificaciones en la barra → 2. Click en una notificacion individual o "Marcar todas como leidas" |

---

## 6. Guia operativa por pantalla

### 6.1 Login (/login/)

- Campos: usuario y contraseña
- Boton "Iniciar sesion"
- Si el usuario ya esta logueado, redirige automaticamente al dashboard

### 6.2 Dashboard (/lab/)

- 5 tarjetas KPI: insumos, reactivos, stock bajo, ordenes pendientes, ordenes en proceso
- Pipeline visual de ordenes por estado
- Tabla de alertas de stock bajo
- Tabla de ultimos 10 movimientos

### 6.3 Categorias (/lab/categories/)

- Tabla con nombre y descripcion
- Botones: Nueva (modal), Editar (modal), Eliminar (confirmacion)
- Soporte HTMX: la tabla se recarga sin refrescar la pagina

### 6.4 Unidades de medida (/lab/uoms/)

- Tabla con nombre y abreviatura
- Misma mecanica que categorias (modales HTMX)

### 6.5 Proveedores (/lab/suppliers/)

- Tabla con nombre, RIF, contacto, telefono, email, estado
- Busqueda por nombre o RIF
- Formulario completo en pagina separada (no modal)

### 6.6 Insumos (/lab/supplies/)

- Tabla con codigo, nombre, categoria, unidad, stock actual, estado
- Busqueda por nombre o codigo
- Indicadores visuales de stock (bajo=rojo, ok=verde, alto=amarillo)
- Click en nombre abre detalle con historial de movimientos

### 6.7 Reactivos (/lab/reagents/)

- Tabla con codigo, nombre, rendimiento, control por lote, estado
- Busqueda por nombre o codigo
- Detalle muestra: ficha + receta (items) + historial de ordenes de produccion
- Desde el detalle se agregan/eliminan items de receta

### 6.8 Movimientos (/lab/movements/)

- Tabla con fecha, insumo, tipo, cantidad, lote, proveedor, motivo, usuario
- Filtros: busqueda por texto y filtro por tipo (entrada/salida/ajuste)
- Formulario de nuevo movimiento en pagina separada

### 6.9 Ordenes de produccion (/lab/orders/)

- Tabla con lote, reactivo, cantidad, estado, creado por, fecha
- Filtro por estado
- Detalle muestra: datos de la orden + insumos necesarios (con stock disponible) + timeline visual del ciclo de vida + movimientos asociados
- Acciones contextuales: Iniciar (si planned), Completar (si in_progress), Cancelar (si planned o in_progress)

---

## 7. Auditoria interna

### 7.1 Analisis de la logica implementada

#### Lo que FUNCIONA correctamente:

**Multi-tenant (aislamiento de datos):** SOLIDO
- Cada query usa `.for_tenant(request.tenant)` — no hay filtraciones entre organizaciones
- Los formularios filtran sus dropdowns por tenant
- El middleware inyecta `request.tenant` automaticamente
- Constraint a nivel de base de datos garantiza que solo superadmins pueden no tener organizacion
- El admin de Django filtra por organizacion
- Auditado y corregido: 7 vulnerabilidades multi-tenant fueron corregidas en mayo 2026

**Calculo de stock:** CORRECTO
- Stock se calcula sumando movimientos (patron event-sourcing), no se guarda como campo editable
- Esto garantiza que el stock siempre es consistente con el historial
- Las salidas se almacenan como negativas, lo que simplifica la suma

**Ciclo de produccion:** LOGICO Y COMPLETO
- Los 4 estados cubren todo el ciclo de vida real
- La verificacion de stock previene iniciar sin insumos suficientes
- La cancelacion revierte consumos con movimientos compensatorios (no elimina los originales), preservando la trazabilidad
- El calculo proporcional de insumos (factor = cantidad / yield) es matematicamente correcto

**Borrado logico:** BIEN IMPLEMENTADO
- Insumos y reactivos usan soft-delete (no se pierden historicos)
- Los movimientos NO se borran nunca (inmutabilidad para auditoria)

**Permisos:** ADECUADOS
- Separacion clara lectura (staff+) vs escritura (admin/manager+)
- Superadmin siempre tiene acceso
- Decoradores reutilizables (`role_required`, `tenant_required`)

#### PROBLEMAS detectados y GAPS funcionales:

**P1 — No hay stock de reactivos producidos (CRITICO FUNCIONAL)**
- El sistema consume insumos al producir pero NO registra la entrada del reactivo producido
- Cuando se completa una OP de "5L de NaOH 0.1M", se restan los insumos pero no hay registro de que ahora hay 5L de NaOH disponible
- El modelo `Reagent` no tiene campo de stock ni movimientos propios
- **Impacto:** Un laboratorio no puede saber cuanto reactivo preparado tiene disponible. El sistema solo es util como gestor de insumos, no como gestor completo de produccion
- **Solucion:** Crear un modelo `ReagentStock` o extender `StockMovement` para incluir productos terminados, o agregar movimientos de "entrada" vinculados al reactivo producido

**P2 — No hay fecha de vencimiento en insumos ni reactivos (ALTO)**
- Un laboratorio clinico trabaja con fechas de caducidad en TODOS sus insumos
- No hay campo `expiration_date` en Supply ni en lotes
- **Impacto:** No se puede alertar sobre insumos proximos a vencer, que es una necesidad critica en un laboratorio clinico regulado
- **Solucion:** Agregar `expiration_date` a `Supply` (o mejor, a nivel de lote/batch)

**P3 — No hay gestion de lotes real (ALTO)**
- Existe `tracks_batch` como flag y `batch_number` como texto libre en movimientos
- Pero no hay un modelo `Batch` que agrupe movimientos de un mismo lote
- No se puede consultar "cuanto queda del lote X" ni "que lotes tengo de insumo Y"
- **Impacto:** La trazabilidad por lote es cosmética — el numero esta ahi, pero no tiene funcionalidad
- **Solucion:** Crear modelo `Batch` con FK a Supply + fecha_vencimiento + stock por lote

**P4 — El stock puede ser negativo sin restriccion (MEDIO)**
- `production_order_start` verifica stock antes de consumir, PERO `StockMovementCreateView` no verifica
- Un admin puede registrar una salida manual mayor que el stock disponible
- **Impacto:** Stock teorico negativo, inconsistencia con la realidad
- **Solucion:** Validacion en el form o en `StockMovement.save()` para salidas

**P5 — Movimientos manuales no se pueden vincular a ordenes (BAJO)**
- `StockMovementCreateView` no expone el campo `production_order` en el form
- Esto es correcto (las salidas automaticas si lo vinculan), pero no se puede registrar una salida manual vinculada a una OP si es necesario

**P6 — No hay reportes ni exportaciones (MEDIO)**
- No hay generacion de PDF (certificados de analisis, reportes de stock)
- No hay exportacion CSV/Excel
- **Impacto:** El personal debe copiar datos manualmente para reportes

**P7 — No hay historial de cambios/audit trail por usuario (MEDIO)**
- Se sabe quien creo un movimiento o una OP, pero no quien edito un insumo o reactivo
- `updated_at` existe pero no `updated_by`
- **Impacto:** No hay trazabilidad completa de quien modifico que

**P8 — No hay password reset (CONOCIDO, en plan L2)**
- Un usuario que olvida su contraseña no puede recuperarla
- Requiere intervencion del admin

**P9 — Notificaciones no se generan automaticamente (BAJO)**
- El modelo `Notification` existe pero no hay signals ni logica que cree notificaciones
- No se notifica automaticamente cuando hay stock bajo, cuando se completa una OP, etc.
- Las notificaciones solo existen si se crean manualmente (via admin o script)

**P10 — Proveedor inactivo NO esta filtrado en el form de movimientos (BAJO)**
- `SupplierForm` no filtra `is_active=True`
- El dropdown de proveedor al crear un movimiento muestra proveedores inactivos

### 7.2 Analisis de factibilidad y utilidad real

#### ¿Es util este sistema para un laboratorio clinico?

**SI, pero con limitaciones importantes.** En su estado actual (v1.0), CMCR Lab es:

**Un buen gestor de insumos (materias primas):**
- Sabe cuanto tiene de cada insumo
- Alerta cuando algo esta bajo
- Registra de donde viene cada insumo (proveedor, lote)
- Documenta cada movimiento

**Un buen planificador de produccion:**
- Define recetas reproducibles
- Calcula automaticamente cuanto insumo necesita
- Verifica disponibilidad antes de producir
- Consume stock automaticamente

**NO es (todavia) un sistema completo de laboratorio clinico:**
- No gestiona el stock de reactivos producidos (P1)
- No controla vencimientos (P2)
- No tiene trazabilidad de lote real (P3)
- No genera certificados de analisis ni reportes (P6)
- No tiene firma electronica ni audit trail completo (P7)

#### Comparacion con alternativas

| Caracteristica | CMCR Lab | Excel/manual | Software de laboratorio comercial |
|---|---|---|---|
| Control de stock insumos | Si | Parcial, propenso a errores | Si |
| Recetas de reactivos | Si (automatico) | Manual | Si |
| Consumo automatico al producir | Si | No | Si |
| Multi-usuario concurrente | Si | No (conflictos de archivo) | Si |
| Vencimientos | No | Manual | Si |
| Certificados de analisis | No | Manual | Si |
| Costo | Incluido en servicio | $0 | $500-5000/mes |
| Personalizacion | Total | Total | Limitada |

#### Conclusion de factibilidad

El sistema es **viable y util como MVP** (Minimo Producto Viable) para un laboratorio que:
1. Necesita salir de Excel para controlar insumos
2. Quiere automatizar el consumo al producir reactivos
3. Necesita que multiples personas accedan a la misma informacion
4. Valora la trazabilidad de movimientos

Para ser un **sistema de laboratorio completo** (LIMS), necesitaria los items P1-P3 y P6 como minimo. Estos conformarian un "Bloque L6" de features clinicas que ya esta planificado.

### 7.3 Priorizacion recomendada de mejoras

| Prioridad | Item | Esfuerzo | Impacto |
|-----------|------|----------|---------|
| 1 | P8: Password reset (L2) | 1.5h | Entregable |
| 2 | P1: Stock de reactivos producidos | 3-4h | Critico funcional |
| 3 | P2: Fechas de vencimiento | 2-3h | Alto para lab clinico |
| 4 | P3: Gestion de lotes real | 3-4h | Alto para trazabilidad |
| 5 | P4: Validacion stock negativo | 1h | Integridad de datos |
| 6 | P9: Notificaciones automaticas | 2h | UX |
| 7 | P6: Reportes PDF/CSV | 4-5h | Operativo |
| 8 | P7: Audit trail por usuario | 2h | Compliance |
| 9 | P10: Filtrar proveedores inactivos | 15min | Calidad |

---

*Documento generado: Mayo 2026*
*Sistema desarrollado por: Ukarasoft Technology (partner: SmartSolutions)*
