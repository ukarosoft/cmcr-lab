# CMCR Lab — Guia Operativa Interna

**Para el equipo SmartSolutions / Ukarasoft**
**Objetivo:** Entender como funciona un laboratorio clinico y como se usa el sistema, para poder capacitar al personal del CMCR y dar soporte tecnico.

---

## Tabla de contenido

1. [Contexto: que hace un laboratorio clinico](#1-contexto-que-hace-un-laboratorio-clinico)
2. [Vocabulario esencial](#2-vocabulario-esencial)
3. [El flujo real de un laboratorio](#3-el-flujo-real-de-un-laboratorio)
4. [Configuracion inicial paso a paso](#4-configuracion-inicial-paso-a-paso)
5. [Ejemplo practico 1: Registrar la compra de insumos](#5-ejemplo-practico-1-registrar-la-compra-de-insumos)
6. [Ejemplo practico 2: Preparar un reactivo (tincion de Wright)](#6-ejemplo-practico-2-preparar-un-reactivo-tincion-de-wright)
7. [Ejemplo practico 3: Preparar una solucion buffer](#7-ejemplo-practico-3-preparar-una-solucion-buffer)
8. [Ejemplo practico 4: Ajuste de inventario por conteo fisico](#8-ejemplo-practico-4-ajuste-de-inventario-por-conteo-fisico)
9. [Ejemplo practico 5: Controlar lotes y vencimientos](#9-ejemplo-practico-5-controlar-lotes-y-vencimientos)
10. [Ejemplo practico 6: Exportar datos para un informe](#10-ejemplo-practico-6-exportar-datos-para-un-informe)
11. [Escenarios especiales](#11-escenarios-especiales)
12. [Mapa completo de funcionalidades](#12-mapa-completo-de-funcionalidades)
13. [Guia de capacitacion al cliente](#13-guia-de-capacitacion-al-cliente)

---

## 1. Contexto: que hace un laboratorio clinico

Un laboratorio clinico analiza muestras biologicas (sangre, orina, heces, etc.) para ayudar a los medicos a diagnosticar enfermedades. El CMCR ofrece estos servicios:

| Servicio | Que analiza | Ejemplo de resultado |
|----------|------------|---------------------|
| **Hematologia** | Sangre completa | Hemoglobina, hematocrito, conteo de globulos blancos/rojos, plaquetas |
| **Grupo sanguineo** | Tipo de sangre | A+, B-, O+, AB+ |
| **Quimica sanguinea** | Sustancias en sangre | Glucosa, urea, creatinina, acido urico |
| **Perfil 20** | 20 parametros quimicos de una vez | Colesterol, trigliceridos, proteinas, enzimas hepaticas, etc. |
| **Serologia** | Anticuerpos e infecciones | VIH, hepatitis, VDRL (sifilis), toxoplasmosis |
| **Orina** | Componentes de la orina | Proteinas, glucosa, celulas, bacterias, pH |
| **Heces** | Parasitos y patogenos | Amebas, giardias, sangre oculta |
| **Marcadores tumorales** | Indicadores de cancer | PSA (prostata), CA-125 (ovario), AFP (higado) |
| **Bacteriologia** | Bacterias en cultivo | Tipo de bacteria, a que antibioticos es sensible |

### ¿Por que necesitan un sistema de inventario?

Para hacer cada uno de esos analisis, el laboratorio necesita **insumos** (cosas que compra) y **reactivos** (cosas que prepara). Si se les acaba un colorante, no pueden hacer hematologias. Si se les vence un kit serologico, los resultados no son confiables.

**El problema real que resolvemos:** Antes del sistema, el CMCR controlaba el inventario en cuadernos o Excel. Esto causaba:
- No saber que se estaba acabando hasta que se acababa
- No saber cuando vencia cada lote
- No poder rastrear de donde vino un reactivo si habia un resultado sospechoso
- Perder tiempo haciendo conteos manuales
- No saber cuanto se gasto en un periodo

---

## 2. Vocabulario esencial

Estos son los terminos que usaran el personal del CMCR y que debemos entender:

### Terminos del laboratorio

| Termino | Que significa | Ejemplo en el sistema |
|---------|--------------|----------------------|
| **Insumo** | Cualquier material que el lab COMPRA | Colorante Wright, Agar sangre, Anti-A |
| **Reactivo** | Producto que el lab PREPARA a partir de insumos | Solucion de Turk, Buffer pH 7.0, Solucion salina 0.85% |
| **Lote** | Grupo de unidades del mismo insumo con el mismo origen | Lote LOT-2026-0847 del Colorante Wright |
| **Fecha de vencimiento** | Hasta cuando el insumo/reactivo es confiable | 2027-03-15 |
| **Stock** | Cantidad disponible en el almacen | 500 mL de Wright |
| **Orden de produccion (OP)** | Documento que autoriza preparar un reactivo | OP para preparar 1 L de solucion de Turk |
| **Receta / BOM** | Lista de insumos y cantidades para preparar un reactivo | Turk = acido acetico + violeta de genciana + agua |
| **Tincion** | Colorante que se aplica a muestras para verlas al microscopio | Wright, Giemsa, Gram |
| **Medio de cultivo** | Sustancia donde se siembran bacterias para que crezcan | Agar sangre, Agar MacConkey |
| **Antisuero** | Reactivo que detecta antigenos especificos en la sangre | Anti-A, Anti-B, Anti-D (para grupo sanguineo) |
| **Kit** | Conjunto comercial listo para usar (no requiere preparacion) | Kit de VDRL, Kit de HIV |
| **Control** | Muestra con valor conocido para verificar que el equipo funciona bien | Control normal, Control patologico |

### Terminos del sistema

| Termino | Que significa |
|---------|--------------|
| **Movimiento de entrada** | Registrar que llego mercancia al almacen |
| **Movimiento de salida** | Registrar que se uso o descarto algo del almacen |
| **Movimiento de ajuste** | Corregir la diferencia entre lo que dice el sistema y lo que hay realmente |
| **Stock minimo** | El nivel en el que el sistema alerta que se necesita comprar mas |
| **Stock maximo** | El nivel maximo recomendado de almacenamiento |
| **Categoria** | Clasificacion del insumo (colorantes, medios de cultivo, etc.) |

---

## 3. El flujo real de un laboratorio

Asi funciona el dia a dia de un laboratorio y como el sistema apoya cada paso:

### Flujo 1: Recibir insumos del proveedor

```
Casa comercial entrega caja con reactivos
         ↓
Encargado del almacen verifica: ¿llego lo que se pidio? ¿los lotes coinciden? ¿las fechas de vencimiento son aceptables?
         ↓
Registra en el sistema: Movimiento de ENTRADA por cada insumo recibido
         ↓
Si el insumo tiene control por lote: crea el LOTE con fecha de vencimiento
         ↓
Stock se actualiza automaticamente
```

**¿Por que importa?** Si llega un frasco de Colorante Wright lote LOT-2026-0847 con vencimiento 2027-03-15, el sistema debe saberlo para:
- Alertar cuando se acerque la fecha de vencimiento
- Poder rastrear ese lote si un resultado sale sospechoso

### Flujo 2: Preparar un reactivo

```
El tecnico necesita Solucion de Turk y ve que se esta acabando
         ↓
Verifica en el sistema que hay stock de los insumos necesarios
         ↓
Crea una ORDEN DE PRODUCCION (OP) en el sistema
         ↓
Hace clic en "Iniciar produccion" — el sistema descuenta los insumos automaticamente
         ↓
El tecnico prepara fisicamente el reactivo en el mesón del laboratorio
         ↓
Cuando termina, hace clic en "Completar" — el sistema registra el reactivo producido
         ↓
El reactivo queda disponible con su stock actualizado
```

**¿Por que importa?** Sin el sistema, el tecnico prepara el reactivo, usa los insumos y nadie actualiza el inventario. Al final del mes, no saben cuanto usaron ni cuanto les queda.

### Flujo 3: Usar un reactivo/insumo diariamente

```
El tecnico necesita 5 mL de Wright para tinciones del dia
         ↓
Saca el frasco del almacen y usa lo que necesita
         ↓
Al final del turno, registra la SALIDA en el sistema
         ↓
(o el encargado registra las salidas del dia en bloque)
```

**Nota para capacitacion:** Este es el punto mas dificil de adopcion. El personal tiende a olvidar registrar las salidas diarias. Si esto pasa, el stock teorico del sistema no coincidira con la realidad. La solucion es hacer conteos fisicos periodicos y ajustar con movimientos de ajuste.

### Flujo 4: Detectar que algo se esta acabando

```
El sistema detecta que un insumo bajo de su stock minimo
         ↓
Genera una NOTIFICACION automatica para administradores y gerentes
         ↓
El administrador ve la alerta en el Dashboard
         ↓
Decide: hacer pedido al proveedor
         ↓
Cuando llega la mercancia, registra la ENTRADA
```

---

## 4. Configuracion inicial paso a paso

Cuando se va a poner en marcha el sistema con el cliente, este es el orden exacto de carga de datos. Cada paso tiene ejemplos reales del CMCR.

### Paso 1: Categorias

Crear las categorias que agrupan los insumos. Estas son las categorias sugeridas para el CMCR:

| Categoria | Que incluye | Ejemplos |
|-----------|-------------|----------|
| Colorantes y tinciones | Colorantes para microscopia | Wright, Giemsa, Gram (cristal violeta, lugol, safranina, alcohol acetona) |
| Reactivos de quimica clinica | Kits y reactivos para analisis quimicos | Glucosa enzimatica, Urea UV, Creatinina, Colesterol |
| Medios de cultivo | Agares y caldos para bacteriologia | Agar sangre, Agar MacConkey, Agar Mueller Hinton, Caldo tioglicolato |
| Antisueros y serologicos | Reactivos para grupo sanguineo y serologia | Anti-A, Anti-B, Anti-D, VDRL carbon, RPR |
| Soluciones y buffers | Soluciones base para preparaciones | Agua destilada, Solucion salina 0.85%, Buffer pH 7.0 |
| Material de control | Sueros y controles de calidad | Control normal, Control patologico, Calibrador |
| Descartables | Material de un solo uso | Lancetas, tubos de ensayo, laminillas, pipetas Pasteur |
| Kits serologicos | Kits comerciales completos | Kit HIV, Kit Hepatitis B, Kit Toxoplasmosis |
| Discos de sensibilidad | Discos antibioticos para antibiogramas | Amoxicilina, Ciprofloxacina, Gentamicina |

### Paso 2: Unidades de medida

| Nombre | Abreviatura | Se usa en |
|--------|-------------|-----------|
| Mililitro | mL | Liquidos: colorantes, soluciones, sueros |
| Litro | L | Grandes volumenes: agua destilada, soluciones |
| Gramo | g | Polvos: sales, agares en polvo |
| Kilogramo | kg | Compras grandes de polvos |
| Unidad | uds | Kits, frascos, cajas |
| Prueba | test | Kits con numero definido de pruebas (ej: kit de 100 tests) |
| Disco | disco | Discos de antibiograma |
| Frasco | fco | Frascos individuales |

### Paso 3: Proveedores

Estos son proveedores tipicos de un laboratorio clinico en Venezuela:

| Nombre | Tipo | Que suministra |
|--------|------|---------------|
| QuimicaLab C.A. | Distribuidor | Reactivos de quimica clinica, kits |
| BioAnalisis | Casa comercial | Medios de cultivo, colorantes |
| MediSupply | Distribuidor | Descartables, material de laboratorio |
| LabTech Internacional | Importador | Equipos y reactivos especializados |
| (Los proveedores reales los proporciona el cliente) | | |

### Paso 4: Insumos (carga masiva)

Esta es una lista ejemplo de insumos tipicos del CMCR organizada por area:

**Hematologia:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| HEM-001 | Colorante Wright | Colorantes y tinciones | mL | 200 | 2000 |
| HEM-002 | Colorante Giemsa | Colorantes y tinciones | mL | 100 | 1000 |
| HEM-003 | Metanol absoluto | Soluciones y buffers | mL | 500 | 5000 |
| HEM-004 | Buffer pH 6.8 | Soluciones y buffers | mL | 200 | 2000 |
| HEM-005 | Aceite de inmersion | Descartables | mL | 50 | 500 |

**Quimica sanguinea:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| QCA-001 | Kit Glucosa enzimatica | Reactivos de quimica clinica | test | 50 | 500 |
| QCA-002 | Kit Urea UV | Reactivos de quimica clinica | test | 50 | 500 |
| QCA-003 | Kit Creatinina | Reactivos de quimica clinica | test | 50 | 500 |
| QCA-004 | Kit Colesterol total | Reactivos de quimica clinica | test | 50 | 500 |
| QCA-005 | Kit Trigliceridos | Reactivos de quimica clinica | test | 50 | 500 |
| QCA-006 | Control normal quimica | Material de control | mL | 10 | 100 |
| QCA-007 | Control patologico quimica | Material de control | mL | 10 | 100 |
| QCA-008 | Calibrador quimica | Material de control | mL | 5 | 50 |

**Grupo sanguineo:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| GS-001 | Antisuero Anti-A | Antisueros y serologicos | mL | 10 | 100 |
| GS-002 | Antisuero Anti-B | Antisueros y serologicos | mL | 10 | 100 |
| GS-003 | Antisuero Anti-D (Rh) | Antisueros y serologicos | mL | 10 | 100 |
| GS-004 | Albumina bovina 22% | Antisueros y serologicos | mL | 10 | 100 |

**Serologia:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| SER-001 | Kit VDRL carbon | Kits serologicos | test | 50 | 500 |
| SER-002 | Kit HIV rapido | Kits serologicos | test | 25 | 200 |
| SER-003 | Kit Hepatitis B (HBsAg) | Kits serologicos | test | 25 | 200 |
| SER-004 | Kit Toxoplasmosis IgG/IgM | Kits serologicos | test | 25 | 100 |

**Orina:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| URI-001 | Tirillas de orina (10 parametros) | Descartables | uds | 100 | 1000 |
| URI-002 | Acido sulfosalicilico 3% | Reactivos de quimica clinica | mL | 50 | 500 |

**Bacteriologia:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| BAC-001 | Agar sangre base | Medios de cultivo | g | 100 | 1000 |
| BAC-002 | Agar MacConkey | Medios de cultivo | g | 100 | 1000 |
| BAC-003 | Agar Mueller Hinton | Medios de cultivo | g | 100 | 1000 |
| BAC-004 | Cristal violeta (Gram) | Colorantes y tinciones | mL | 50 | 500 |
| BAC-005 | Lugol (Gram) | Colorantes y tinciones | mL | 50 | 500 |
| BAC-006 | Alcohol acetona (Gram) | Colorantes y tinciones | mL | 100 | 1000 |
| BAC-007 | Safranina (Gram) | Colorantes y tinciones | mL | 50 | 500 |
| BAC-008 | Discos Amoxicilina | Discos de sensibilidad | disco | 50 | 500 |
| BAC-009 | Discos Ciprofloxacina | Discos de sensibilidad | disco | 50 | 500 |

**Descartables:**

| Codigo | Nombre | Categoria | Unidad | Stock min | Stock max |
|--------|--------|-----------|--------|-----------|-----------|
| DES-001 | Tubos tapa lila (EDTA) | Descartables | uds | 100 | 1000 |
| DES-002 | Tubos tapa roja (seco) | Descartables | uds | 100 | 1000 |
| DES-003 | Lancetas retractiles | Descartables | uds | 100 | 1000 |
| DES-004 | Laminillas portaobjetos | Descartables | uds | 100 | 2000 |
| DES-005 | Laminillas cubreobjetos | Descartables | uds | 100 | 2000 |
| DES-006 | Pipetas Pasteur | Descartables | uds | 50 | 500 |

### Paso 5: Registrar stock inicial

Para cada insumo, crear un movimiento de **Entrada** con la cantidad actual en el almacen. Motivo sugerido: "Carga de stock inicial".

### Paso 6: Definir reactivos con recetas

Los reactivos son cosas que el laboratorio prepara. Ejemplos:

**Reactivo: Solucion de Turk** (para conteo de leucocitos en hematologia)

- Rendimiento: 100 mL
- Receta:
  - Acido acetico glacial: 1 mL
  - Violeta de genciana 1%: 1 mL
  - Agua destilada: 98 mL

**Reactivo: Buffer fosfato pH 6.8** (para tincion de Wright)

- Rendimiento: 1000 mL (1 L)
- Receta:
  - Fosfato monobasico de potasio (KH2PO4): 6.63 g
  - Fosfato dibasico de sodio (Na2HPO4): 2.56 g
  - Agua destilada: 1000 mL

**Reactivo: Solucion salina 0.85%** (para diversas pruebas)

- Rendimiento: 1000 mL (1 L)
- Receta:
  - Cloruro de sodio (NaCl): 8.5 g
  - Agua destilada: 1000 mL

**Reactivo: Lugol parasitologico** (para observacion de parasitos en heces)

- Rendimiento: 100 mL
- Receta:
  - Yodo metalico: 1 g
  - Yoduro de potasio: 2 g
  - Agua destilada: 100 mL

**Nota importante:** No todos los reactivos se preparan internamente. Muchos kits comerciales (HIV, Hepatitis, Glucosa) vienen listos para usar y se registran como **insumos**, no como reactivos. Solo lo que el laboratorio mezcla/prepara en su meson va como reactivo.

---

## 5. Ejemplo practico 1: Registrar la compra de insumos

### Escenario

Llego un pedido del proveedor QuimicaLab con:
- 2 frascos de Colorante Wright (500 mL cada uno = 1000 mL total)
- 1 kit de Glucosa enzimatica (200 tests)
- 1 kit de VDRL (100 tests)

### Pasos en el sistema

**Movimiento 1: Colorante Wright**
1. Ir a **Movimientos > Nuevo**
2. Insumo: Colorante Wright
3. Tipo: **Entrada**
4. Cantidad: **1000** (mL)
5. Numero de lote: LOT-2026-0512 (viene impreso en los frascos)
6. Proveedor: QuimicaLab C.A.
7. Motivo: "Compra pedido #47 - Mayo 2026"
8. Guardar

**Lote del Wright (si aplica):**
1. Ir a **Lotes > Nuevo**
2. Insumo: Colorante Wright
3. Numero de lote: LOT-2026-0512
4. Fecha de vencimiento: 2027-08-15 (viene en el frasco)
5. Proveedor: QuimicaLab C.A.
6. Notas: "2 frascos de 500 mL"
7. Guardar

**Movimiento 2: Kit Glucosa**
1. Insumo: Kit Glucosa enzimatica
2. Tipo: Entrada
3. Cantidad: 200 (tests)
4. Proveedor: QuimicaLab C.A.
5. Motivo: "Compra pedido #47 - Mayo 2026"

**Movimiento 3: Kit VDRL**
1. Insumo: Kit VDRL carbon
2. Tipo: Entrada
3. Cantidad: 100 (tests)
4. Proveedor: QuimicaLab C.A.
5. Motivo: "Compra pedido #47 - Mayo 2026"

### Resultado

El Dashboard reflejara inmediatamente el nuevo stock de estos tres insumos. Si alguno estaba en alerta de "stock bajo", la alerta desaparecera si el nuevo stock supera el minimo.

---

## 6. Ejemplo practico 2: Preparar un reactivo (tincion de Wright)

### Contexto para nosotros

La tincion de Wright es el colorante mas usado en hematologia. Se aplica sobre una gota de sangre extendida en una laminilla (frotis sanguineo) para poder ver los globulos rojos, blancos y plaquetas bajo el microscopio. Cada hemograma que hace el laboratorio consume un poco de Wright.

El Wright comercial se compra listo para usar (es un insumo, no un reactivo). Pero el **buffer para Wright** si se prepara en el laboratorio (es un reactivo). El buffer es necesario porque despues de aplicar el colorante, se agrega el buffer para que la tincion funcione correctamente.

### Escenario

El tecnico ve que le quedan solo 100 mL de Buffer pH 6.8 (el minimo es 200 mL). Necesita preparar 1 litro.

### Paso 1: Verificar stock de insumos

Antes de crear la orden, el tecnico puede ir a **Insumos** y verificar:
- Fosfato monobasico de potasio: ¿hay al menos 6.63 g?
- Fosfato dibasico de sodio: ¿hay al menos 2.56 g?
- Agua destilada: ¿hay al menos 1000 mL?

### Paso 2: Crear la orden de produccion

1. Ir a **Produccion > Nueva orden**
2. Reactivo: Buffer fosfato pH 6.8
3. Numero de lote: BUF-2026-05-001
4. Cantidad: 1000 (mL — coincide con el rendimiento de la receta, asi que el factor es 1x)
5. Observaciones: "Para tinciones de Wright — stock mensual"
6. Guardar

La orden se crea en estado **Planificada**.

### Paso 3: Revisar el detalle

En el detalle de la orden, el sistema muestra:
- Fosfato monobasico de potasio: necesita 6.63 g — disponible: 45 g ✓
- Fosfato dibasico de sodio: necesita 2.56 g — disponible: 30 g ✓
- Agua destilada: necesita 1000 mL — disponible: 8000 mL ✓

Todos los indicadores estan en verde. Se puede iniciar.

### Paso 4: Iniciar produccion

1. Clic en **"Iniciar produccion"**
2. El sistema descuenta automaticamente:
   - 6.63 g de Fosfato monobasico
   - 2.56 g de Fosfato dibasico
   - 1000 mL de Agua destilada
3. Estado cambia a **En proceso**

El tecnico ahora prepara fisicamente el buffer en el meson: pesa las sales, las disuelve en agua, ajusta el pH, filtra si es necesario.

### Paso 5: Completar produccion

Cuando el buffer esta listo y almacenado:
1. Clic en **"Completar"**
2. El sistema:
   - Crea un lote nuevo del Buffer pH 6.8
   - Registra la entrada de 1000 mL al stock del reactivo
   - Estado cambia a **Completada**

### Resultado

- Los tres insumos tienen stock actualizado (reducido)
- El reactivo Buffer pH 6.8 tiene 1100 mL de stock (100 anteriores + 1000 nuevos)
- Queda documentado quien lo preparo, cuando, y con que insumos

---

## 7. Ejemplo practico 3: Preparar una solucion buffer

### Contexto para nosotros

La solucion salina al 0.85% es una de las soluciones mas basicas y mas usadas en el laboratorio. Se usa como diluyente en multiples pruebas: grupo sanguineo (para lavar globulos rojos), serologia (para diluir sueros), microbiologia (para hacer suspensiones bacterianas), etc.

Es extremadamente facil de preparar (solo sal y agua) pero se consume en grandes cantidades, asi que siempre debe haber stock.

### Escenario

Se necesitan 5 litros de solucion salina 0.85%.

### Paso 1: Crear la orden

1. Reactivo: Solucion salina 0.85%
2. Numero de lote: SS-2026-05-003
3. Cantidad: **5000** (mL)
4. Observaciones: "Stock semanal para multiples areas"

**Calculo automatico del sistema:**
La receta rinde 1000 mL. Se piden 5000 mL. Factor = 5000/1000 = 5x.
- NaCl: 8.5 g x 5 = **42.5 g**
- Agua destilada: 1000 mL x 5 = **5000 mL**

### Paso 2: Iniciar, preparar, completar

Mismo flujo que el ejemplo anterior. Al completar, el stock del reactivo "Solucion salina 0.85%" aumenta en 5000 mL.

### ¿Por que importa este ejemplo?

Demuestra el calculo proporcional del sistema. Si la receta base es para 1 litro pero el tecnico necesita 5 litros, no tiene que hacer la multiplicacion mental — el sistema lo hace automaticamente y descuenta las cantidades correctas.

---

## 8. Ejemplo practico 4: Ajuste de inventario por conteo fisico

### Contexto para nosotros

En la practica, el stock teorico del sistema rara vez coincide al 100% con la realidad. Razones tipicas:
- Se uso un insumo y nadie lo registro (la causa mas comun)
- Derrame accidental
- Un frasco se rompio
- Error al registrar la cantidad en un movimiento anterior
- Evaporacion de solventes volatiles

**El conteo fisico** es cuando alguien va al almacen, cuenta/mide todo, y compara con lo que dice el sistema.

### Escenario

Conteo fisico de fin de mes. Resultado:

| Insumo | Sistema dice | Fisicamente hay | Diferencia |
|--------|-------------|-----------------|------------|
| Colorante Wright | 850 mL | 780 mL | -70 mL |
| Agar sangre base | 300 g | 300 g | 0 (ok) |
| Kit VDRL | 45 tests | 52 tests | +7 tests |
| Agua destilada | 15000 mL | 14200 mL | -800 mL |

### Pasos en el sistema

**Ajuste 1: Colorante Wright**
1. Ir a **Movimientos > Nuevo**
2. Insumo: Colorante Wright
3. Tipo: **Ajuste**
4. Cantidad: **-70** (negativo porque falta)
5. Motivo: "Ajuste por conteo fisico mayo 2026. Probable consumo no registrado durante tinciones diarias."

**Ajuste 2: Kit VDRL**
1. Tipo: Ajuste
2. Cantidad: **+7** (positivo porque hay mas de lo esperado)
3. Motivo: "Ajuste por conteo fisico mayo 2026. Posible error en registro de entrada anterior."

**Ajuste 3: Agua destilada**
1. Tipo: Ajuste
2. Cantidad: **-800**
3. Motivo: "Ajuste por conteo fisico mayo 2026. Consumo no registrado en preparaciones diarias y enjuagues."

El Agar no necesita ajuste porque coincide.

### ¿Con que frecuencia se hacen conteos fisicos?

Depende del laboratorio. Recomendacion:
- **Semanal:** los 5-10 insumos mas usados (Wright, agua destilada, solucion salina)
- **Mensual:** inventario completo
- **Inmediato:** si un resultado clinico parece sospechoso y se quiere verificar la trazabilidad del reactivo

---

## 9. Ejemplo practico 5: Controlar lotes y vencimientos

### Contexto para nosotros

En un laboratorio clinico, usar un reactivo vencido puede dar resultados erroneos. Un resultado erroneo puede significar un diagnostico equivocado. Por eso, el control de vencimientos no es opcional — es una obligacion.

**Ejemplo real de riesgo:** Si el Kit de HIV esta vencido, puede dar falsos negativos (decirle a un paciente que no tiene HIV cuando si lo tiene). Esto puede tener consecuencias graves.

### Escenario

Llego un pedido con tres kits serologicos:

| Kit | Lote | Vencimiento |
|-----|------|-------------|
| Kit HIV rapido | HIV-2026-A045 | 2027-01-15 |
| Kit Hepatitis B | HBV-2026-B012 | 2026-09-30 |
| Kit Toxoplasmosis | TOXO-2026-C008 | 2027-06-20 |

### Paso 1: Registrar las entradas (3 movimientos)

Igual que el ejemplo 1. Un movimiento de entrada por cada kit.

### Paso 2: Crear los lotes

Para cada kit, ir a **Lotes > Nuevo**:

**Lote 1:**
- Insumo: Kit HIV rapido
- Numero de lote: HIV-2026-A045
- Fecha de vencimiento: 2027-01-15
- Proveedor: QuimicaLab C.A.
- Notas: "25 tests por kit"

(Repetir para los otros dos kits)

### Paso 3: Monitorear vencimientos

El Dashboard mostrara automaticamente:
- **En agosto 2026:** Alerta de que el Kit Hepatitis B (lote HBV-2026-B012) vencera el 30 de septiembre (faltan ~30 dias)
- **Despues del 30 de septiembre:** Se marcara como **VENCIDO** en la lista de lotes

### ¿Que hacer con un lote vencido?

1. **No usarlo** — descartarlo segun el procedimiento del laboratorio
2. Registrar una **Salida** del insumo con motivo "Descarte por vencimiento - Lote HBV-2026-B012"
3. Hacer el pedido de reposicion al proveedor

### Filtros utiles en la lista de lotes

- **Vencidos:** muestra todos los lotes con fecha pasada — para descarte
- **Por vencer:** muestra lotes que vencen en los proximos 30 dias — para planificar compras

---

## 10. Ejemplo practico 6: Exportar datos para un informe

### Contexto para nosotros

El laboratorio puede necesitar reportes para:
- Rendir cuentas a la gerencia del clinico sobre cuanto se gasto
- Justificar pedidos de compra
- Auditorias de calidad
- Declaraciones fiscales (facturas de proveedores)

### Escenario

El jefe del laboratorio necesita un informe de consumo del mes para la gerencia del clinico.

### Pasos

1. Ir a **Movimientos**
2. Clic en **"Exportar CSV"**
3. Se descarga un archivo `movimientos.csv`
4. Abrir en Excel
5. Filtrar por fecha (columna de fecha >= 01/05/2026 y <= 31/05/2026)
6. Filtrar por tipo = "Salida"
7. Resultado: todas las salidas del mes, con insumo, cantidad, quien lo registro, motivo

### Exportaciones disponibles

| Archivo | Para que sirve |
|---------|---------------|
| `supplies.csv` | Lista de todos los insumos con su stock actual — util para inventario valorizado |
| `movements.csv` | Historial completo de movimientos — util para reportes de consumo |
| `orders.csv` | Todas las ordenes de produccion — util para medir productividad |
| `batches.csv` | Todos los lotes con vencimiento — util para auditorias de calidad |

---

## 11. Escenarios especiales

### Escenario: Se derramo un frasco

Un tecnico derramo accidentalmente un frasco de 500 mL de metanol:
1. Registrar **Salida** de 500 mL de Metanol absoluto
2. Motivo: "Derrame accidental en area de hematologia"
3. Si esto deja el stock por debajo del minimo, el sistema generara una alerta automatica

### Escenario: El proveedor envio el insumo equivocado

Se registro una entrada de 200 tests de Kit Glucosa, pero en realidad eran tests de Urea:
1. Registrar **Ajuste** de -200 en Kit Glucosa — motivo: "Correccion: proveedor envio Urea, no Glucosa"
2. Registrar **Entrada** de 200 en Kit Urea — motivo: "Correccion: mercancia correspondiente a pedido #47"

No se puede editar el movimiento original, pero los ajustes corrigen el stock.

### Escenario: Cancelar una produccion a mitad de proceso

Se inicio una OP de 2 litros de solucion salina, pero el tecnico se equivoco en el procedimiento y hay que descartarlo:
1. Ir al detalle de la orden
2. Clic en **"Cancelar"**
3. El sistema devuelve automaticamente los insumos que habia descontado
4. El tecnico puede crear una nueva OP e intentar de nuevo

Los insumos se devuelven con movimientos compensatorios — no se pierde nada.

### Escenario: Un resultado clinico es sospechoso y quieren rastrear el reactivo

El medico reporta que los resultados de glucosa de un paciente no tienen sentido. El jefe del laboratorio quiere verificar:
1. Ir a **Insumos > Kit Glucosa enzimatica > Detalle**
2. Ver el historial de movimientos para saber que lote se esta usando actualmente
3. Verificar la fecha de vencimiento del lote en **Lotes**
4. Verificar si el control de calidad del dia fue normal

Esto demuestra el valor de la trazabilidad: poder rastrear desde el resultado hasta el insumo, el lote y el proveedor.

### Escenario: Dos areas del laboratorio usan el mismo insumo

Hematologia y bacteriologia usan agua destilada. Ambas registran sus salidas contra el mismo insumo. El stock refleja el consumo total. Si es necesario separar el consumo por area, pueden usar el campo "Motivo" para indicar el area: "Consumo semanal - Bacteriologia".

---

## 12. Mapa completo de funcionalidades

| Funcionalidad | Donde | Quien puede | Ejemplo |
|---------------|-------|-------------|---------|
| Ver dashboard con KPIs | `/lab/` | Todos | "¿Cuantos insumos estan en stock bajo?" |
| Crear/editar categorias | `/lab/categories/` | Admin, Gerente | Crear "Medios de cultivo" |
| Crear/editar unidades | `/lab/uoms/` | Admin, Gerente | Crear "mL" |
| Crear/editar proveedores | `/lab/suppliers/` | Admin, Gerente | Registrar "QuimicaLab C.A." |
| Crear/editar insumos | `/lab/supplies/` | Admin, Gerente | Registrar "Colorante Wright" |
| Ver detalle de insumo | `/lab/supplies/<id>/` | Todos | Ver stock y movimientos de Wright |
| Crear/editar reactivos | `/lab/reagents/` | Admin, Gerente | Definir "Solucion de Turk" |
| Agregar items a receta | `/lab/reagents/<id>/` | Admin, Gerente | Agregar "Acido acetico: 1 mL" a Turk |
| Ver detalle de reactivo | `/lab/reagents/<id>/` | Todos | Ver receta y stock del reactivo |
| Registrar movimientos | `/lab/movements/new/` | Admin, Gerente | Entrada de 1000 mL de Wright |
| Ver historial de movimientos | `/lab/movements/` | Todos | Buscar salidas del mes |
| Crear lotes | `/lab/batches/new/` | Admin, Gerente | Lote LOT-2026-0847 del Wright |
| Ver lotes y vencimientos | `/lab/batches/` | Todos | Filtrar lotes por vencer |
| Crear ordenes de produccion | `/lab/orders/new/` | Admin, Gerente | OP para 1 L de Buffer pH 6.8 |
| Iniciar/completar/cancelar OP | `/lab/orders/<id>/` | Admin, Gerente | "Iniciar produccion" |
| Ver notificaciones | Barra superior | Todos | "Stock bajo de Wright: 80 mL" |
| Exportar CSV | Boton en cada lista | Admin, Gerente | Descargar lista de insumos |
| Recuperar contrasena | `/password-reset/` | Todos | "Olvide mi contrasena" |

---

## 13. Guia de capacitacion al cliente

### Estructura sugerida de la capacitacion (2 sesiones de 1.5 horas)

**Sesion 1: Conceptos y configuracion**
1. Que es el sistema y por que les facilita la vida (15 min)
   - Comparar con lo que hacen ahora (cuaderno/Excel)
   - Mostrar el dashboard con datos de ejemplo
2. Acceso y roles (10 min)
   - Cada quien con su usuario
   - Diferencia entre lo que puede hacer un admin vs un empleado
3. Configuracion inicial juntos (45 min)
   - Crear categorias reales del CMCR
   - Crear unidades de medida
   - Registrar sus proveedores
   - Registrar 10-15 insumos principales de cada area
4. Carga de stock inicial (20 min)
   - Registrar la cantidad actual de los insumos cargados

**Sesion 2: Operacion diaria**
1. Registrar entradas cuando llega mercancia (15 min)
   - Ejercicio: simular que llego un pedido
2. Crear un reactivo con receta (15 min)
   - Ejercicio: definir una solucion que preparan regularmente
3. Crear y ejecutar una orden de produccion (20 min)
   - Ejercicio: planificar → iniciar → completar
4. Ajustes de inventario (10 min)
   - Cuando y como corregir diferencias
5. Lotes y vencimientos (10 min)
   - Crear lotes, ver alertas
6. Notificaciones y exportaciones (10 min)
7. Preguntas y dudas (10 min)

### Errores comunes a prevenir durante la capacitacion

| Error | Consecuencia | Como prevenirlo |
|-------|-------------|-----------------|
| No registrar salidas diarias | Stock del sistema no coincide con la realidad | Establecer rutina: al final del turno, registrar consumos |
| Confundir "insumo" con "reactivo" | Registrar un kit comercial como reactivo (no necesita receta) | Regla simple: si lo compra tal cual, es insumo. Si lo prepara, es reactivo |
| No registrar lotes | Pierde trazabilidad | Siempre anotar el numero de lote del frasco/kit |
| Registrar cantidad en unidad equivocada | Stock descuadrado (ej: registrar 1 litro como 1 mL) | Verificar la unidad del insumo antes de registrar |
| No poner motivo en los movimientos | Pierde informacion del contexto | Hacer obligatorio en la practica, aunque el campo sea opcional |

### Materiales de apoyo sugeridos

- Imprimir el Manual de Usuario (docs/MANUAL_USUARIO.md) para el laboratorio
- Crear una hoja plastificada de referencia rapida con los pasos mas frecuentes:
  1. Como registrar una entrada (4 pasos)
  2. Como registrar una salida (4 pasos)
  3. Como crear una orden de produccion (5 pasos)

---

*Documento interno — SmartSolutions / Ukarasoft Technology*
*Version 1.0 — Mayo 2026*
*No distribuir al cliente final*
