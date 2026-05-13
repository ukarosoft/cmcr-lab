# CMCR Lab — Manual de Usuario

**Sistema de Gestion de Inventario y Produccion de Reactivos**
**Centro Clinico Madre Carmen Rendiles**
**Version:** 2.0 — Mayo 2026

---

## Tabla de contenido

1. [Introduccion](#1-introduccion)
2. [Acceso al sistema](#2-acceso-al-sistema)
3. [Pantalla principal (Dashboard)](#3-pantalla-principal-dashboard)
4. [Roles de usuario](#4-roles-de-usuario)
5. [Configuracion inicial](#5-configuracion-inicial)
6. [Gestion de insumos](#6-gestion-de-insumos)
7. [Gestion de reactivos y recetas](#7-gestion-de-reactivos-y-recetas)
8. [Movimientos de inventario](#8-movimientos-de-inventario)
9. [Lotes y vencimientos](#9-lotes-y-vencimientos)
10. [Ordenes de produccion](#10-ordenes-de-produccion)
11. [Notificaciones](#11-notificaciones)
12. [Exportacion de datos](#12-exportacion-de-datos)
13. [Recuperacion de contrasena](#13-recuperacion-de-contrasena)
14. [Preguntas frecuentes](#14-preguntas-frecuentes)

---

## 1. Introduccion

CMCR Lab es el sistema del laboratorio para llevar el control de todo lo que se compra, se almacena, se usa y se produce. Permite:

- Saber en todo momento cuanto hay de cada insumo y reactivo
- Registrar cada entrada y salida del almacen
- Definir las recetas de los reactivos que se preparan internamente
- Crear ordenes de produccion que descuentan los insumos automaticamente
- Recibir alertas cuando algo esta por acabarse o proximo a vencer
- Exportar datos a Excel/CSV para reportes
- Controlar lotes y fechas de vencimiento

El sistema funciona desde cualquier computador o celular con navegador web. No requiere instalar nada.

---

## 2. Acceso al sistema

### Iniciar sesion

1. Abra el navegador y vaya a la direccion del sistema
2. Ingrese su **usuario** y **contrasena**
3. Presione **"Ingresar al sistema"**

El sistema lo llevara directamente al panel principal (Dashboard).

### Cerrar sesion

Haga clic en su nombre de usuario en la esquina superior derecha y seleccione **"Cerrar sesion"**.

### Olvide mi contrasena

1. En la pantalla de inicio de sesion, haga clic en **"¿Olvidaste tu contrasena?"**
2. Ingrese su correo electronico registrado
3. Revise su bandeja de entrada (y la carpeta de spam) — recibira un enlace
4. Haga clic en el enlace y escriba su nueva contrasena dos veces
5. Listo. Ya puede iniciar sesion con la nueva contrasena

El enlace expira despues de una hora. Si no le llega el correo, contacte al administrador.

---

## 3. Pantalla principal (Dashboard)

Al iniciar sesion, vera un resumen de la situacion actual del laboratorio:

### Indicadores principales (KPIs)

- **Total de insumos** — cuantos insumos diferentes tiene registrados
- **Total de reactivos** — cuantos reactivos tiene definidos
- **Stock bajo** — cuantos insumos o reactivos estan por debajo de su nivel minimo
- **Ordenes pendientes** — cuantas ordenes de produccion estan planificadas esperando ser iniciadas
- **En produccion** — cuantas ordenes estan en proceso actualmente

### Secciones del Dashboard

- **Pipeline de produccion** — muestra cuantas ordenes hay en cada estado (planificada, en proceso, completada, cancelada)
- **Alertas de stock bajo** — lista de insumos y reactivos que necesitan reabastecimiento
- **Lotes proximos a vencer** — lotes que venceran en los proximos 30 dias
- **Movimientos recientes** — los ultimos 10 movimientos de inventario registrados

---

## 4. Roles de usuario

El sistema tiene tres niveles de acceso:

| Rol | Que puede hacer | Quien lo usa |
|-----|----------------|--------------|
| **Administrador** | Todo: crear, editar, eliminar, producir, exportar | Director del laboratorio, jefe de area |
| **Gerente** | Lo mismo que el administrador | Supervisor, jefe de turno |
| **Empleado** | Solo puede ver informacion (consultas) | Tecnicos, personal auxiliar |

**Importante:** Si usted tiene rol de Empleado y necesita registrar algo, solicite a su supervisor o administrador que lo haga, o que le asigne un rol con permisos de escritura.

---

## 5. Configuracion inicial

Antes de empezar a usar el sistema, el administrador debe crear los datos base en este orden:

### Paso 1: Categorias

Vaya a **Inventario > Categorias** y cree las clasificaciones de sus insumos. Ejemplos:

- Colorantes y tinciones
- Reactivos de quimica clinica
- Medios de cultivo
- Antisueros y serologicos
- Soluciones y buffers
- Material de control
- Descartables

### Paso 2: Unidades de medida

Vaya a **Inventario > Unidades de medida** y registre las unidades que utiliza. Ejemplos:

| Nombre | Abreviatura |
|--------|-------------|
| Mililitro | mL |
| Litro | L |
| Gramo | g |
| Kilogramo | kg |
| Unidad | uds |
| Prueba | test |
| Frasco | fco |

### Paso 3: Proveedores

Vaya a **Inventario > Proveedores** y registre las casas comerciales y distribuidores. Campos disponibles:

- Nombre (obligatorio)
- RIF
- Persona de contacto
- Telefono
- Correo electronico
- Direccion
- Estado activo/inactivo

Un proveedor marcado como **inactivo** no aparecera en los formularios de registro de entradas.

### Paso 4: Insumos

Vaya a **Inventario > Insumos** y registre cada materia prima o reactivo que compra. Vea la seccion 6 para mas detalle.

### Paso 5: Stock inicial

Registre la cantidad actual de cada insumo mediante movimientos de **Entrada**. Vea la seccion 8.

### Paso 6: Reactivos y recetas

Si el laboratorio prepara reactivos internamente, defina cada reactivo y su receta. Vea la seccion 7.

---

## 6. Gestion de insumos

### ¿Que es un insumo?

Un insumo es cualquier material que el laboratorio compra para su funcionamiento: reactivos comerciales, colorantes, medios de cultivo, soluciones preparadas, material de control, etc.

### Crear un insumo

Vaya a **Inventario > Insumos > Nuevo** y complete:

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| Codigo | Identificador interno | INS-001 |
| Nombre | Nombre del insumo | Colorante Wright |
| Descripcion | Detalle tecnico | Colorante para frotis sanguineo, frasco 500 mL |
| Categoria | Clasificacion | Colorantes y tinciones |
| Unidad de medida | Como se mide | mL |
| Stock minimo | Alerta si baja de este valor | 200 |
| Stock maximo | Capacidad maxima de almacenamiento | 2000 |
| Control por lote | Si necesita rastrear lotes | Si |
| Activo | Si esta en uso actualmente | Si |

### Entender el stock

El stock de un insumo **no se escribe a mano**. El sistema lo calcula automaticamente sumando todas las entradas y restando todas las salidas. Esto garantiza que el numero siempre coincide con el historial de movimientos.

### Estados de stock

- **Bajo** (indicador rojo) — el stock actual esta por debajo del minimo. Necesita reabastecimiento.
- **OK** (indicador verde) — el stock esta en un nivel normal.
- **Alto** (indicador amarillo) — el stock supera el maximo definido.

### Ver detalle de un insumo

Haga clic en el nombre de un insumo para ver:
- Su ficha completa con todos los datos
- El historial de los ultimos 50 movimientos (entradas, salidas, ajustes)

### Eliminar un insumo

Al eliminar un insumo, este se oculta de las listas pero **no se pierde la informacion**. Los movimientos historicos se conservan. Si necesita reactivarlo, contacte al administrador.

---

## 7. Gestion de reactivos y recetas

### ¿Que es un reactivo en este sistema?

Un reactivo es un producto que el laboratorio **prepara internamente** a partir de insumos. Por ejemplo: una tincion de Gram preparada a partir de sus componentes individuales, o una solucion buffer preparada a partir de sales y agua destilada.

### Crear un reactivo

Vaya a **Reactivos > Nuevo** y complete:

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| Codigo | Identificador interno | REA-001 |
| Nombre | Nombre del reactivo | Solucion de Turk |
| Descripcion | Para que se usa | Solucion para conteo de leucocitos |
| Instrucciones de preparacion | Procedimiento paso a paso | Disolver 1 mL de acido acetico glacial... |
| Cantidad producida | Cuanto se obtiene por preparacion | 100 |
| Unidad de rendimiento | En que unidad | mL |
| Stock minimo | Alerta si baja de este valor | 50 |
| Stock maximo | Referencia de capacidad | 500 |

### Definir la receta

Despues de crear el reactivo, entre a su **detalle** y agregue los insumos necesarios:

1. Haga clic en **"Agregar insumo a la receta"**
2. Seleccione el insumo, la cantidad necesaria y la unidad
3. Repita para cada insumo de la receta

**Ejemplo:** Solucion de Turk (rinde 100 mL)
- Acido acetico glacial: 1 mL
- Violeta de genciana 1%: 1 mL
- Agua destilada: 98 mL

Cuando cree una orden de produccion por 500 mL, el sistema multiplicara automaticamente:
- Acido acetico glacial: 5 mL
- Violeta de genciana 1%: 5 mL
- Agua destilada: 490 mL

### Stock de reactivos

Al igual que los insumos, los reactivos tienen stock que se calcula automaticamente. Cuando se completa una orden de produccion, el sistema registra la entrada del reactivo producido.

---

## 8. Movimientos de inventario

### ¿Que es un movimiento?

Un movimiento es el registro de que algo entro, salio o se ajusto en el inventario. Cada movimiento queda grabado permanentemente — no se puede editar ni borrar, para garantizar la trazabilidad.

### Tipos de movimiento

| Tipo | Cuando se usa | Efecto en stock |
|------|---------------|-----------------|
| **Entrada** | Llego mercancia del proveedor | Suma |
| **Salida** | Se uso o descarto un insumo | Resta |
| **Ajuste** | Conteo fisico no coincide con el sistema | Suma o resta |

### Registrar un movimiento

Vaya a **Movimientos > Nuevo** y complete:

| Campo | Descripcion |
|-------|-------------|
| Insumo | Seleccione el insumo que se mueve |
| Tipo | Entrada, Salida o Ajuste |
| Cantidad | Cuanto (siempre en numero positivo) |
| Numero de lote | Lote del proveedor (si aplica) |
| Proveedor | Quien lo suministro (solo para entradas) |
| Orden de produccion | Si el movimiento esta relacionado con una OP |
| Motivo | Razon del movimiento (ej: "Compra mensual", "Descarte por vencimiento") |

### Proteccion contra stock negativo

El sistema **no permite** registrar una salida mayor al stock disponible. Si intenta sacar 500 mL de un insumo que solo tiene 200 mL, el formulario mostrara un error indicando el stock disponible.

### Movimientos automaticos

Cuando se inicia una orden de produccion, el sistema genera automaticamente las salidas de cada insumo. Estos movimientos automaticos quedan vinculados a la orden y no necesita registrarlos manualmente.

---

## 9. Lotes y vencimientos

### ¿Que es un lote?

Un lote agrupa una cantidad especifica de un insumo o reactivo que comparte el mismo origen (proveedor, fecha de fabricacion, numero de lote del fabricante). Controlar lotes permite:

- Saber cuanto queda de un lote especifico
- Rastrear de donde vino un insumo si hay un problema
- Controlar fechas de vencimiento por lote

### Crear un lote

Vaya a **Lotes > Nuevo** y complete:

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| Insumo | A que insumo pertenece | Colorante Wright |
| Numero de lote | Codigo del fabricante/proveedor | LOT-2026-0847 |
| Fecha de vencimiento | Cuando expira | 2027-03-15 |
| Proveedor | Quien lo suministro | QuimicaLab C.A. |
| Notas | Observaciones | Frasco de 500 mL, almacenar a temperatura ambiente |

### Alertas de vencimiento

El Dashboard muestra automaticamente los lotes que venceran en los proximos 30 dias. Los lotes ya vencidos se resaltan para que tome accion inmediata (descarte, devolucion o evaluacion).

### Filtros en la lista de lotes

La lista de lotes permite filtrar por:
- **Vencidos** — lotes cuya fecha de vencimiento ya paso
- **Por vencer** — lotes que venceran en los proximos 30 dias

---

## 10. Ordenes de produccion

### ¿Que es una orden de produccion?

Una orden de produccion (OP) documenta el proceso de preparar un reactivo. Registra que se va a preparar, cuanto, cuando, quien lo hizo y que insumos se usaron.

### Ciclo de vida de una orden

Una orden pasa por estos estados:

```
PLANIFICADA  →  EN PROCESO  →  COMPLETADA
                    ↓
                CANCELADA
```

### Crear una orden

Vaya a **Produccion > Nueva orden** y complete:

| Campo | Descripcion | Ejemplo |
|-------|-------------|---------|
| Reactivo | Que va a preparar | Solucion de Turk |
| Numero de lote | Identificador de esta preparacion | TURK-2026-05-001 |
| Cantidad | Cuanto va a preparar | 500 |
| Observaciones | Notas del proceso | Preparacion para stock mensual |

La orden se crea en estado **Planificada**.

### Ver detalle de la orden

En el detalle de la orden puede ver:
- Datos de la orden (reactivo, cantidad, estado, fechas)
- Lista de insumos necesarios con la cantidad requerida y el stock disponible de cada uno
- Si todos los insumos tienen stock suficiente (indicadores verdes) o si falta algo (indicadores rojos)
- Timeline visual del progreso de la orden

### Iniciar produccion

1. Abra el detalle de la orden
2. Verifique que todos los insumos tienen stock suficiente (indicadores verdes)
3. Haga clic en **"Iniciar produccion"**

El sistema automaticamente:
- Descuenta de cada insumo la cantidad necesaria segun la receta
- Cambia el estado a **En proceso**
- Registra la fecha y hora de inicio

**Si no hay stock suficiente** de algun insumo, el sistema le indicara cual falta y cuanto necesita. No podra iniciar la produccion hasta resolver el faltante.

### Completar produccion

Cuando el reactivo este preparado y listo:

1. Abra el detalle de la orden
2. Haga clic en **"Completar"**

El sistema automaticamente:
- Crea un lote nuevo del reactivo producido
- Registra la entrada del reactivo al inventario (la cantidad producida)
- Cambia el estado a **Completada**
- Registra la fecha y hora de finalizacion

### Cancelar una orden

Si necesita cancelar una orden:

1. Abra el detalle de la orden
2. Haga clic en **"Cancelar"**

**Si la orden estaba en proceso**, el sistema devuelve automaticamente los insumos que se habian descontado (crea movimientos de entrada compensatorios). Nada se pierde.

**Si la orden estaba planificada**, simplemente se marca como cancelada (no habia consumido nada).

---

## 11. Notificaciones

El sistema genera notificaciones automaticas cuando ocurren eventos importantes:

### Notificaciones automaticas

- **Stock bajo** — cuando un insumo o reactivo baja de su nivel minimo despues de un movimiento
- **Orden completada** — cuando una orden de produccion se completa exitosamente
- **Orden cancelada** — cuando una orden de produccion se cancela

### Ver notificaciones

- El icono de campana en la barra superior muestra cuantas notificaciones sin leer tiene
- Haga clic en el icono para ver la lista
- Puede marcar notificaciones como leidas individualmente o todas a la vez

---

## 12. Exportacion de datos

El sistema permite exportar datos a archivos CSV (compatibles con Excel) para generar reportes externos.

### Exportaciones disponibles

| Exportacion | Que incluye | Donde encontrarla |
|-------------|-------------|-------------------|
| Insumos | Lista completa con stock actual, categoria, unidad | Inventario > Insumos > Exportar CSV |
| Movimientos | Historial de todos los movimientos | Movimientos > Exportar CSV |
| Ordenes | Todas las ordenes de produccion | Produccion > Exportar CSV |
| Lotes | Lista de lotes con stock y vencimiento | Lotes > Exportar CSV |

### Como exportar

1. Vaya a la seccion correspondiente
2. Haga clic en el boton **"Exportar CSV"**
3. Se descargara un archivo que puede abrir con Excel, Google Sheets o LibreOffice

---

## 13. Recuperacion de contrasena

Si olvido su contrasena:

1. Vaya a la pantalla de inicio de sesion
2. Haga clic en **"¿Olvidaste tu contrasena?"**
3. Ingrese el correo electronico asociado a su cuenta
4. Revise su bandeja de entrada (tambien la carpeta de spam)
5. Haga clic en el enlace del correo
6. Escriba su nueva contrasena dos veces
7. Haga clic en **"Cambiar contrasena"**

**Notas:**
- El enlace de recuperacion es valido por 1 hora
- Si no recibe el correo, verifique que el correo ingresado es el correcto
- Por seguridad, el sistema no informa si el correo existe o no en la base de datos
- Si sigue sin poder acceder, contacte al administrador del sistema

---

## 14. Preguntas frecuentes

### ¿Por que no puedo editar un movimiento?

Los movimientos son inmutables por diseno. Esto garantiza que el historial es confiable y auditable. Si cometio un error, registre un movimiento de ajuste para corregir la diferencia.

### ¿Que pasa si el stock del sistema no coincide con el conteo fisico?

Registre un movimiento de tipo **Ajuste** con la diferencia. Por ejemplo: si el sistema dice 500 mL pero fisicamente hay 450 mL, registre un ajuste de -50 mL con el motivo "Ajuste por conteo fisico".

### ¿Puedo eliminar un insumo que ya tiene movimientos?

Si. Al "eliminar" un insumo, este se oculta de las listas pero toda su informacion historica se conserva. Los movimientos existentes no se afectan.

### ¿Que pasa si intento iniciar una produccion sin stock suficiente?

El sistema le mostrara exactamente que insumos faltan y cuanto necesita de cada uno. No podra iniciar la produccion hasta que el stock sea suficiente.

### ¿Puedo cancelar una orden que ya esta en proceso?

Si. Al cancelar una orden en proceso, el sistema devuelve automaticamente todos los insumos que se habian descontado. Es seguro cancelar en cualquier momento.

### ¿Quien puede ver mis movimientos?

Solo los usuarios de su misma institucion pueden ver los datos. Cada usuario ve unicamente la informacion de su centro.

### ¿Puedo usar el sistema desde el celular?

Si. El sistema se adapta a pantallas de cualquier tamano. Puede acceder desde el navegador de su celular o tablet.

### ¿Como se que un lote esta por vencer?

El Dashboard muestra automaticamente los lotes que venceran en los proximos 30 dias. Ademas, puede ir a **Lotes** y filtrar por "Por vencer" o "Vencidos".

---

*Centro Clinico Madre Carmen Rendiles*
*Sistema desarrollado por SmartSolutions*
*Version 2.0 — Mayo 2026*
