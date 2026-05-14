# CMCR Lab -- Guia de primer uso y pruebas funcionales

**URL:** https://cmcr-lab-ss.onrender.com
**Usuario:** `admin` / `CMCRadmin2026!`

> Nota: el Free tier de Render duerme tras 15 min de inactividad. La primera carga puede tardar ~30 segundos.

---

## Paso 0 -- Login y primer vistazo

1. Ir a https://cmcr-lab-ss.onrender.com/login/
2. Ingresar `admin` / `CMCRadmin2026!`
3. Deberia redirigir al **Dashboard** con KPIs:
   - Total de insumos registrados
   - Total de reactivos
   - Ordenes pendientes
   - Ordenes en progreso
   - Alertas de stock bajo (insumos y reactivos)
   - Lotes proximos a vencer

**Verificar:**
- [ ] El menu de usuario (avatar arriba a la derecha) se abre al hacer clic y se cierra al hacer clic fuera
- [ ] El toggle de modo oscuro/claro funciona
- [ ] El chip de organizacion muestra "Centro Clinico Madre Carmen Rendiles"

---

## Paso 1 -- Datos base (Catalogos)

Antes de usar el sistema hay que tener categorias, unidades de medida y proveedores. Los datos demo ya vienen precargados, pero vamos a verificar y crear uno nuevo de cada uno.

### 1.1 Categorias

**Ruta:** Menu lateral > Categorias (o `/lab/categories/`)

1. Ver la lista -- deberia haber categorias demo (Reactivo base, Solvente, etc.)
2. Clic en **"Nueva categoria"**
3. Llenar: Nombre = `Colorantes`, Descripcion = `Tinciones para microbiologia`
4. Guardar

**Verificar:**
- [ ] La categoria aparece en la lista
- [ ] Se puede editar (cambiar descripcion)
- [ ] Se puede eliminar (si no tiene insumos asociados)

### 1.2 Unidades de medida

**Ruta:** Menu lateral > Unidades de medida (o `/lab/uoms/`)

1. Ver la lista -- deberia haber unidades demo (mL, L, g, unidad, etc.)
2. Clic en **"Nueva unidad"**
3. Llenar: Nombre = `Frasco`, Abreviatura = `fco`
4. Guardar

**Verificar:**
- [ ] La unidad aparece en la lista
- [ ] Se puede editar y eliminar

### 1.3 Proveedores

**Ruta:** Menu lateral > Proveedores (o `/lab/suppliers/`)

1. Ver la lista -- deberian existir proveedores demo
2. Clic en **"Nuevo proveedor"**
3. Llenar:
   - Nombre: `LabQuim Venezuela`
   - Contacto: `Carlos Perez`
   - Telefono: `0414-5551234`
   - Email: `ventas@labquim.com`
   - Activo: Si
4. Guardar

**Verificar:**
- [ ] El proveedor aparece en la lista
- [ ] Se puede editar
- [ ] Se puede desactivar (desmarcar "Activo") -- un proveedor inactivo NO debe aparecer al crear movimientos de stock

---

## Paso 2 -- Insumos (materias primas)

**Ruta:** Menu lateral > Insumos (o `/lab/supplies/`)

Los insumos son las materias primas que el laboratorio compra: acido clorhidrico, suero fisiologico, tubos de ensayo, etc.

### 2.1 Crear un insumo

1. Clic en **"Nuevo insumo"**
2. Llenar:
   - Nombre: `Acido clorhidrico 37%`
   - Categoria: `Reactivo base` (o la que exista)
   - Unidad de medida: `mL`
   - Stock minimo: `500`
   - Stock maximo: `5000`
   - Proveedor: `LabQuim Venezuela` (el que creamos)
3. Guardar

**Verificar:**
- [ ] El insumo aparece en la lista con stock = 0
- [ ] El indicador de stock muestra "bajo" o alerta (porque 0 < 500)
- [ ] Clic en el nombre lleva al **detalle** con historial de movimientos vacio

### 2.2 Ver detalle de insumo

En la vista de detalle de cualquier insumo:
- [ ] Se ve el stock actual
- [ ] Se ve el historial de movimientos (vacio si es nuevo)
- [ ] Se ven los datos del proveedor

---

## Paso 3 -- Movimientos de stock

**Ruta:** Menu lateral > Movimientos (o `/lab/movements/`)

Los movimientos registran entradas, salidas y ajustes de inventario.

### 3.1 Registrar una entrada (compra)

1. Clic en **"Nuevo movimiento"**
2. Llenar:
   - Insumo: `Acido clorhidrico 37%`
   - Tipo: `Entrada`
   - Cantidad: `2000`
   - Numero de lote: `LOTE-HCl-2026-001`
   - Razon/nota: `Compra inicial proveedor LabQuim`
3. Guardar

**Verificar:**
- [ ] El movimiento aparece en la lista
- [ ] Volver a Insumos > Acido clorhidrico: el stock ahora muestra **2000 mL**
- [ ] El indicador cambio a "OK" (2000 esta entre 500 y 5000)
- [ ] En el detalle del insumo, el historial muestra el movimiento

### 3.2 Registrar una salida (consumo)

1. Nuevo movimiento
2. Llenar:
   - Insumo: `Acido clorhidrico 37%`
   - Tipo: `Salida`
   - Cantidad: `300`
   - Razon: `Uso en preparacion de reactivo Tincion Gram`
3. Guardar

**Verificar:**
- [ ] Stock del insumo ahora = **1700 mL** (2000 - 300)

### 3.3 Validacion de stock negativo (P4)

1. Intentar crear un movimiento de **salida** con cantidad mayor al stock actual
   - Insumo: `Acido clorhidrico 37%` (stock = 1700)
   - Tipo: `Salida`
   - Cantidad: `5000`
2. Guardar

**Verificar:**
- [ ] El formulario debe **rechazar** el movimiento con un error tipo "Stock insuficiente"
- [ ] El movimiento NO se crea

### 3.4 Ajuste de inventario

1. Nuevo movimiento
   - Insumo: `Acido clorhidrico 37%`
   - Tipo: `Ajuste`
   - Cantidad: `-200` (negativa = correccion hacia abajo)
   - Razon: `Correccion por inventario fisico`
2. Guardar

**Verificar:**
- [ ] Stock ahora = **1500 mL** (1700 - 200)

---

## Paso 4 -- Reactivos (productos que fabrica el lab)

**Ruta:** Menu lateral > Reactivos (o `/lab/reagents/`)

Los reactivos son soluciones o preparados que el laboratorio **produce** a partir de insumos. Ejemplo: "Tincion Gram" se hace mezclando cristal violeta + lugol + alcohol-acetona + safranina.

### 4.1 Crear un reactivo

1. Clic en **"Nuevo reactivo"**
2. Llenar:
   - Nombre: `Tincion Gram`
   - Descripcion: `Kit completo para tincion diferencial Gram`
   - Unidad de rendimiento: `mL`
   - Stock minimo: `100`
   - Stock maximo: `2000`
3. Guardar

### 4.2 Agregar insumos al reactivo (receta)

En el detalle del reactivo recien creado:
1. En la seccion "Insumos necesarios", clic en **"Agregar insumo"**
2. Seleccionar:
   - Insumo: `Acido clorhidrico 37%`
   - Cantidad necesaria: `50` (mL por cada lote que se produzca)
3. Guardar
4. Repetir para otros insumos si existen

**Verificar:**
- [ ] El reactivo muestra la lista de insumos (receta) con cantidades
- [ ] Se puede eliminar un insumo de la receta
- [ ] El stock del reactivo es 0 (aun no se ha producido)

---

## Paso 5 -- Ordenes de produccion (flujo completo)

**Ruta:** Menu lateral > Ordenes de produccion (o `/lab/orders/`)

Este es el flujo mas importante del sistema. Una orden de produccion consume insumos y genera stock del reactivo.

### 5.1 Crear orden

1. Clic en **"Nueva orden"**
2. Llenar:
   - Reactivo: `Tincion Gram`
   - Cantidad a producir: `500`
   - Numero de lote: `GRAM-2026-001`
   - Notas: `Produccion de mayo`
3. Guardar

**Verificar:**
- [ ] La orden aparece en la lista con estado **"Planificada"**
- [ ] En el detalle se ven los datos de la orden

### 5.2 Iniciar produccion

1. En el detalle de la orden, clic en **"Iniciar produccion"**

**Verificar:**
- [ ] El estado cambia a **"En progreso"**
- [ ] Se crean movimientos de SALIDA para cada insumo de la receta
- [ ] Revisar stock del insumo: deberia haber bajado en la cantidad de la receta
   - Acido clorhidrico: 1500 - 50 = **1450 mL**

### 5.3 Completar produccion (P1 -- el fix mas critico)

1. En el detalle de la orden en progreso, clic en **"Completar"**

**Verificar:**
- [ ] El estado cambia a **"Completada"**
- [ ] Se crea automaticamente un **lote** del reactivo (ir a Lotes para verificar)
- [ ] Se crea un movimiento de **ENTRADA** del reactivo con la cantidad producida
- [ ] Ir a Reactivos > Tincion Gram: el stock ahora es **500 mL**
- [ ] En el dashboard, si no hay otras alertas, Tincion Gram deberia mostrar stock OK

### 5.4 Cancelar una orden (prueba aparte)

1. Crear otra orden para el mismo reactivo
2. Iniciarla (esto consume insumos)
3. Cancelarla

**Verificar:**
- [ ] El estado cambia a **"Cancelada"**
- [ ] Los insumos consumidos se **devuelven** (movimientos de entrada compensatorios)
- [ ] El stock de los insumos vuelve al valor anterior
- [ ] NO se crea stock del reactivo

---

## Paso 6 -- Lotes y vencimientos (P2, P3)

**Ruta:** Menu lateral > Lotes (o `/lab/batches/`)

### 6.1 Lote creado automaticamente

Si completaste la orden del Paso 5.3:
- [ ] Deberia existir un lote `GRAM-2026-001` asociado al reactivo `Tincion Gram`

### 6.2 Crear lote manual

1. Clic en **"Nuevo lote"**
2. Llenar:
   - Insumo O Reactivo (solo uno): seleccionar `Acido clorhidrico 37%`
   - Numero de lote: `HCl-2026-MAYO`
   - Fecha de vencimiento: poner una fecha cercana (ej: manana)
   - Proveedor: `LabQuim Venezuela`
   - Notas: `Lote de prueba vencimiento`
3. Guardar

**Verificar:**
- [ ] El lote aparece en la lista
- [ ] Si la fecha es cercana o pasada, deberia aparecer alerta en el **Dashboard** ("Lotes proximos a vencer")
- [ ] El lote muestra si esta vencido o cuantos dias faltan

---

## Paso 7 -- Notificaciones (P9)

**Ruta:** Icono de campana en la barra superior

Las notificaciones se generan automaticamente cuando:
- Un insumo llega a stock bajo
- Una orden de produccion se completa o cancela

**Verificar:**
- [ ] Si algun insumo tiene stock bajo, deberia haber notificaciones
- [ ] Al hacer clic en una notificacion se puede marcar como leida
- [ ] Existe opcion "Marcar todas como leidas"

---

## Paso 8 -- Exportaciones CSV (P6)

Desde los listados de insumos, movimientos, ordenes y lotes hay un boton de exportar.

1. Ir a Insumos > clic en **"Exportar CSV"**
2. Ir a Movimientos > clic en **"Exportar CSV"**
3. Ir a Ordenes > clic en **"Exportar CSV"**
4. Ir a Lotes > clic en **"Exportar CSV"**

**Verificar:**
- [ ] Cada exportacion descarga un archivo .csv
- [ ] Abrir en Excel/LibreOffice: los datos corresponden a lo que se ve en pantalla
- [ ] Solo contiene datos de la organizacion CMCR (no de otras orgs)

---

## Paso 9 -- Recuperacion de contrasena (P8)

1. Cerrar sesion (avatar > Cerrar sesion)
2. En la pantalla de login, clic en **"Olvidaste tu contrasena?"**
3. Ingresar el email del usuario (`admin@cmcr.local`)
4. El sistema muestra "Te hemos enviado un correo"

**Nota:** Actualmente el email backend es `console` (no envia emails reales). En produccion con SMTP configurado, llegaria un correo con link de reset. Para esta prueba solo verificar que:
- [ ] El formulario de reset se muestra correctamente
- [ ] Al enviar un email muestra la pagina de confirmacion
- [ ] No revela si el email existe o no (seguridad)

---

## Paso 10 -- UI general

### 10.1 Modo oscuro/claro
- [ ] Clic en el icono de sol/luna en la barra superior
- [ ] El tema cambia inmediatamente
- [ ] Refrescar la pagina: el tema se mantiene (localStorage)

### 10.2 Responsive
- [ ] Reducir la ventana del navegador a tamano movil
- [ ] La barra de navegacion se adapta
- [ ] Las tablas se pueden hacer scroll horizontal

### 10.3 Menu de usuario
- [ ] Clic en el avatar (letra del nombre) arriba a la derecha
- [ ] Se despliega menu con nombre del usuario y rol
- [ ] Clic en "Cerrar sesion" cierra la sesion y redirige a login
- [ ] Clic fuera del menu lo cierra

---

## Resumen de verificaciones por modulo

| Modulo | Checkpoints | Estado |
|--------|------------|--------|
| Login/Logout | Login OK, avatar menu, cerrar sesion | |
| Dashboard | KPIs, alertas stock bajo, lotes vencimiento | |
| Categorias | CRUD completo | |
| Unidades de medida | CRUD completo | |
| Proveedores | CRUD + desactivar | |
| Insumos | CRUD + detalle + stock | |
| Movimientos | Entrada, salida, ajuste, validacion negativo | |
| Reactivos | CRUD + receta de insumos | |
| Ordenes de produccion | Crear, iniciar, completar, cancelar | |
| Lotes | Automaticos + manuales, vencimientos | |
| Notificaciones | Stock bajo, OP completada/cancelada | |
| Exportaciones CSV | 4 exports, datos correctos | |
| Password reset | Formulario funciona, no leak de emails | |
| UI | Dark mode, responsive, menu avatar | |

---

## Errores conocidos / limitaciones actuales

1. **Email:** El backend es `console` -- no envia emails reales. Password reset no funciona end-to-end hasta configurar SMTP.
2. **Free tier Render:** El servidor duerme tras 15 min sin uso. La primera peticion despues tarda ~30s.
3. **Sin HTTPS estricto:** Render provee HTTPS pero no hay HSTS configurado.
4. **Sin rate limiting en login:** Se puede intentar contrasenas sin limite (pendiente django-ratelimit).
