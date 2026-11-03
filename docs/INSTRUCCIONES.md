# Instrucciones del proyecto — Huffman Web Compressor

> Documento de referencia permanente. Antes de escribir o cambiar código se revisa este archivo.
> Si algo no aparece aquí, **no se hace** hasta acordarlo con el equipo.

---

## 1. Reglas de trabajo (acordadas por el equipo)

1. **Construcción por bloques.** El código se divide en bloques pequeños e independientes (ver `docs/PLAN.md`). Cada bloque tiene su archivo, su responsable y su tarea en el backlog.
2. **Nada de código extra.** Solo se programa lo que pide la actividad. Los extras se discuten después, cuando lo obligatorio esté terminado.
3. **Lo más sencillo posible.** Se prefiere la solución más corta y fácil de explicar que cumpla el requisito. Sin abstracciones, patrones o librerías innecesarias.
4. **Todo documentado.** Cada bloque lleva comentarios claros en español y su explicación en la documentación.
5. **El equipo debe poder explicar todo.** Si una parte no se puede explicar en voz alta frente al profesor, se simplifica.
6. **Metodología Scrum.** Hay entregas semanales al profesor. El backlog vive en GitHub Projects y cada tarea muestra su avance real en el tiempo.
7. **Cada integrante sube su propio bloque.** Cada quien hace commits y PR de los apartados que le tocan, desde su cuenta de GitHub, para que el historial muestre la participación de todos.
8. **Fechas reales.** El historial de GitHub y del tablero refleja las fechas reales de trabajo. No se alteran fechas.
9. **Prioridad actual:** presentar **la mitad del proyecto** el **jueves 5 de noviembre de 2026** (Sprint 0 + Sprint 1 del backlog). Los archivos se suben a GitHub el martes 3 y el miércoles 4. Entrega final: **12 de noviembre de 2026** (por confirmar).
10. **Fichas de entrega.** Cada archivo nuevo o modificado se entrega con una ficha que indica: responsable, ruta en el repo, rama, mensaje de commit, revisor y cómo mover su tarjeta del tablero. Las fichas se guardan en `para_el_equipo/ENTREGAS.md`.
11. **Los integrantes hacen todo en GitHub.** Ellos crean el repo, las tarjetas del backlog, las ramas, los commits, los PR y los movimientos del tablero. Claude solo prepara los archivos y las fichas; no sube nada.
12. **Plan completo y verificado antes de repartir.** Todo el proyecto (todos los sprints) se programa y se prueba completo antes de entregar fichas. Así ningún bloque entregado necesita cambios después: los sprints siguientes solo **agregan** código, no corrigen.
13. **Código lo más sencillo y al punto**, con comentarios en español que expliquen el *por qué* de cada paso del algoritmo.

---

## 2. Requisitos de la actividad (resumen fiel del enunciado)

### 2.1 Generales
- Equipo de máximo 4 integrantes (el mismo de la actividad anterior).
- Tecnología libre (elegida: Python + Streamlit, ver `docs/PLAN.md`).
- Aplicación **desplegada con URL pública**.
- **Prohibido pagar** hosting, dominio, API, base de datos o cualquier servicio.
- Huffman **implementado por el equipo**. Prohibido usar ZIP, gzip, rar, 7z, zlib u otra biblioteca de compresión.

### 2.2 Entrada de texto
- **A) Archivo local:** subir un `.txt`.
- **B) Project Gutenberg:** buscar por título, autor o palabras clave, elegir una obra en texto y usarla como entrada. No hace falta guardar el repositorio de Gutenberg.

### 2.3 Huffman (pasos obligatorios)
1. Calcular la frecuencia de cada símbolo.
2. Construir el árbol con la estrategia voraz (cola de prioridad).
3. Generar el código binario de cada símbolo.
4. Codificar el contenido.
5. Generar un **archivo comprimido real**.
6. Descomprimir ese archivo.
7. Recuperar **exactamente** el contenido original, **sin depender del `.txt` original**.

### 2.4 Formato de archivo propio
- Extensión propia (propuesta: **`.hfa`**, ver `docs/PLAN.md`).
- Debe estar documentado y contener como mínimo:
  - identificación o versión del formato;
  - información para reconstruir el árbol o los códigos;
  - datos comprimidos;
  - bits válidos del último byte (o un mecanismo equivalente);
  - tamaño original;
  - metadatos adicionales pertinentes.
- **No vale** guardar el texto original dentro del archivo.

### 2.5 Métricas (después de comprimir)
- Tamaño original en bytes y KB/MB.
- Tamaño comprimido en bytes y KB/MB.
- Bytes/KB/MB ahorrados.
- Porcentaje de reducción.
- Razón de compresión (opcional).
- Número de símbolos diferentes.

### 2.6 Visualización
- Tabla de frecuencias.
- Código binario de cada símbolo.
- Árbol de Huffman.

### 2.7 Inspector del archivo comprimido
Al cargar **solo** el archivo comprimido debe mostrar:
- nombre y extensión;
- versión/formato;
- tamaño original y comprimido;
- bytes/KB/MB ahorrados y porcentaje de compresión;
- número de símbolos;
- tabla de frecuencias (o equivalente);
- códigos Huffman reconstruidos;
- árbol de Huffman reconstruido;
- total de bits codificados;
- vista parcial y legible de los datos binarios.

Después, con un botón explícito: **DESCOMPRIMIR**, ver el texto recuperado y **descargarlo** como `.txt`.
El inspector primero muestra la estructura; el texto original solo aparece tras descomprimir.

### 2.8 Descompresión e integridad
- Flujo: `original.txt → archivo.hfa → recuperado.txt`.
- El recuperado debe ser idéntico al original.
- Mecanismo de verificación: **hash SHA-256** guardado en el encabezado.

### 2.9 Interfaz
Flujo visible: **BUSCAR LIBRO / SUBIR TXT → ANALIZAR → CONSTRUIR HUFFMAN → COMPRIMIR → INSPECCIONAR → DESCARGAR / DESCOMPRIMIR**.
Diseño libre. Se valora que ayude a entender el algoritmo.

### 2.10 GitHub (repositorio)
Debe contener: código fuente, `README.md`, documentación del formato, pruebas y evidencias, URL del deployment, instrucciones de ejecución, integrantes, descripción del algoritmo, resultados de compresión, tecnologías, **uso de IA y herramientas**, limitaciones conocidas.
El historial de commits debe mostrar la evolución y la participación de todos.

### 2.11 GitHub Projects
- Columnas: **Backlog → Por hacer → En progreso → En revisión → Terminado**.
- Cada tarea indica: qué se hará, responsable, resultado esperado y estado.
- Incluir trabajo algorítmico y de ingeniería (frecuencias, cola de prioridad, árbol, códigos, empaquetado de bits, formato, descompresor, inspector, Gutenberg, interfaz, pruebas, deployment, documentación).

### 2.12 Pruebas mínimas (documentadas)
1. Texto pequeño (frecuencias y códigos comprobables a mano).
2. Libro de Project Gutenberg.
3. Integridad (comprimir → descomprimir → idéntico).
4. Archivo no usado durante el desarrollo.

El profesor puede llevar un `.txt` nuevo para una prueba en vivo.

### 2.13 Sección 13
Falta en el documento que recibimos (se salta de la 12 a la 14). **Pendiente: pedirla al profesor.**

### 2.14 Entregable de planeación
1. Nombre del equipo e integrantes.
2. URL del repositorio.
3. URL de GitHub Projects.
4. Evidencia breve de reunión y toma de decisiones.
5. Backlog inicial con responsables.
6. Tecnología seleccionada.
7. Extensión propuesta.
8. Boceto de la aplicación.
9. Propuesta de estructura del archivo comprimido.

### 2.15 Entrega final
1. URL pública de la app.
2. URL del repositorio.
3. URL de GitHub Projects.
4. README completo y documentación del formato.
5. Evidencias de pruebas e integridad en el repositorio.
6. Reporte técnico breve en PDF (Guía de Reportes).

### 2.16 Pendiente de la Act. 5 original
La Act. 5 pedía además **"el algoritmo de expansión mínima"** (Prim o Kruskal) y una GUI en Python. Como las actividades se unieron, la GUI web cubre la parte de interfaz. **Por confirmar con el profesor** si el árbol de expansión mínima sigue siendo obligatorio. No se programa hasta confirmarlo.

---

## 3. Matriz de cumplimiento

Cada requisito de la actividad indica qué bloque o tarea lo cumple, cómo se verificó y en qué sprint se entrega.
✅ = programado y probado el 3 nov 2026 · 📄 = documento o tarea del equipo (no es código).

| Req. | Requisito | Dónde se cumple | Verificación | Sprint |
|---|---|---|---|---|
| 1 | Huffman propio, sin zlib/gzip/zip | `huffman/` usa solo `heapq`, `struct`, `hashlib` | ✅ Revisión de imports | 1 |
| 1 | URL pública gratuita | B12-01 Streamlit Community Cloud | 📄 Al desplegar | 1 |
| 2A | Subir `.txt` local | `app.py` → `seccion_entrada` | ✅ Navegador: `abra.txt` | 1 |
| 2B | Buscar en Gutenberg por título, autor o palabra clave | `huffman/gutenberg.py` → `buscar` (catálogo OPDS oficial) | ✅ "quijote", "Mary Shelley", "pirates", "ballena" (< 1 s) | 2 |
| 2B | Elegir obra y usarla como entrada | `gutenberg.descargar` + botón "Usar este libro" | ✅ Navegador: #2000 y #84 | 2 |
| 3.1 | Frecuencias | B1 `frecuencias.py` | ✅ `test_frecuencias` | 1 |
| 3.2 | Árbol voraz con cola de prioridad | B2 `arbol.py` | ✅ `test_codigos_calculados_a_mano` | 1 |
| 3.3 | Códigos binarios | B3 `codigos.py` | ✅ `test_ningun_codigo_es_prefijo_de_otro` | 1 |
| 3.4–3.5 | Codificar y generar archivo real | B4 `bits.py` + B5 `formato.py` + B6 `comprimir` | ✅ Descarga de `pg2000.hfa` | 1 |
| 3.6–3.7 | Descomprimir y recuperar exacto, sin el `.txt` | B6 `descomprimir` | ✅ 6 casos borde + 5 libros idénticos | 1 |
| 4 | Extensión propia | `.hfa` | ✅ | 1 |
| 4 | Versión del formato | Firma `HUFA` + versión 1 | ✅ `test_campos_del_encabezado` | 1 |
| 4 | Info para reconstruir el árbol | Tabla de frecuencias | ✅ | 1 |
| 4 | Bits válidos del último byte | Campos "total de bits" y "bits del último byte" | ✅ | 1 |
| 4 | Tamaño original y metadatos | Tamaño, nombre original, SHA-256 | ✅ | 1 |
| 4 | No guardar el texto original | Solo bits empaquetados | ✅ `test_no_guarda_el_texto_original` | 1 |
| 4 | Formato documentado | `docs/FORMATO.md` con ejemplo hexadecimal | 📄 D-02 | 1 |
| 5 | Tamaños en bytes y KB/MB, ahorro, %, razón, símbolos | B6 `metricas` + `mostrar_metricas` | ✅ Quijote: 2.12 MB → 1.21 MB, 42.92 % | 1 |
| 6 | Tabla de frecuencias | `visual.tabla` en sección 2 | ✅ | 1 |
| 6 | Código de cada símbolo | `visual.tabla` con códigos en sección 3 | ✅ | 1 |
| 6 | Árbol de Huffman | `visual.arbol_a_dot` + `st.graphviz_chart` (sección 3.3) | ✅ 227 nodos (Quijote) | 2 |
| 6 / 9 | Creatividad: entender cómo se construye el árbol | Sección 3.1: deslizador paso a paso con la cola de prioridad y la unión resaltada (`construir_arbol(..., pasos)` + `visual.bosque_en_paso`) | ✅ `test_la_cola_coincide_con_el_orden_real_de_salida`; navegador con "abracadabra" (4 pasos) y Quijote (113 pasos) | 2 |
| 6 / 9 | Creatividad: cómo se forma un código | Sección 3.3: elegir un símbolo resalta su camino en rojo y lo explica (`visual.camino`) | ✅ `test_camino_de_un_simbolo`; navegador "b → 110" | 2 |
| 6 / 9 | Creatividad: relación frecuencia ↔ longitud del código | Sección 3.2: gráfica de barras de frecuencia coloreada por bits | ✅ Navegador | 2 |
| 7 | Inspector: nombre, extensión, versión, tamaños, ahorro, %, símbolos, total de bits | `app.py` → `seccion_inspector` (metadatos) | ✅ Navegador con `pg2000.hfa` | 1 |
| 7 | Inspector: tabla de frecuencias, códigos y árbol reconstruidos | `seccion_inspector` (estructura) | ✅ | 2 |
| 7 | Inspector: vista parcial de los bits | `visual.bits_legibles` | ✅ | 2 |
| 7 | Botón DESCOMPRIMIR, ver texto y descargar `.txt` | `seccion_inspector` | ✅ Descarga con SHA-256 idéntico | 1 |
| 7 | Primero estructura, después descompresión | El texto solo aparece tras el botón | ✅ | 1 |
| 8 | Verificar integridad | SHA-256 en el encabezado | ✅ `test_detecta_archivo_danado` | 1 |
| 9 | Flujo visible en la interfaz | Encabezado con los pasos + secciones numeradas 1–6 | ✅ | 1 |
| 9 | Demostración en vivo legible | Opción "Escribir un texto corto" (por ejemplo `abracadabra`) para ver el árbol completo | ✅ Navegador | 2 |
| 10 | Repo con README, formato, pruebas, URL, ejecución, integrantes, algoritmo, resultados, tecnologías, uso de IA, limitaciones | D-01 (Sprint 1) y D-03 (Sprint 3) | 📄 | 1 y 3 |
| 10 | Commits de todo el equipo | Fichas en `para_el_equipo/ENTREGAS.md` | 📄 | Todos |
| 11 | GitHub Projects con 5 columnas y tareas completas | P-03 + `para_el_equipo/TARJETAS_BACKLOG.md` | 📄 | 0 |
| 12.1 | Prueba con texto pequeño | B11 `TextoPequeno` + `docs/FORMATO.md` §3 | ✅ | 1 |
| 12.2 | Prueba con libro de Gutenberg | T-01 (evidencias) | ✅ técnica / 📄 evidencia | 3 |
| 12.3 | Prueba de integridad | B11 `Integridad` + T-03 | ✅ técnica / 📄 evidencia | 1 y 3 |
| 12.4 | Archivo no usado en el desarrollo | T-02 | 📄 | 3 |
| 14 | Entregable de planeación (9 puntos) | P-01 a P-08 | 📄 | 0 |
| 15 | Entrega final (6 puntos), con reporte PDF | D-03, D-04, R-03 | 📄 | 3 |
| Act. 5 | Árbol de expansión mínima | X-01 (por confirmar con el profesor) | ❓ | — |

### Limitaciones conocidas (para el README)
- En textos muy pequeños el `.hfa` pesa más que el original, porque el encabezado ocupa más que el ahorro.
- Los bits se procesan como texto `"0101"` para que el código sea fácil de explicar. Esto usa ~5 bytes de memoria por cada byte del original, así que se recomiendan archivos de hasta ~20 MB.
- La búsqueda de Gutenberg muestra los primeros 25 resultados.
- En Streamlit Community Cloud la app se suspende tras varias horas sin uso y tarda unos segundos en despertar.

---

## 4. Criterio central (lo que se evalúa)
Demostrar que el equipo entiende cómo Huffman convierte:
**frecuencias → árbol → códigos → binario almacenable → inspección → reconstrucción sin el original.**

Flujo que la app debe demostrar:
**ANALIZAR → COMPRIMIR → MEDIR → INSPECCIONAR → DESCOMPRIMIR → VERIFICAR**
