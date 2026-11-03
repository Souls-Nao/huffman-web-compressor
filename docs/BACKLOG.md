# Backlog — Huffman Web Compressor

Product Backlog completo, de principio a fin, ordenado por sprint.
Cada fila se convierte en un **Issue** de GitHub con título `[ID] Tarea` y se agrega a **GitHub Projects**.

- **Estados:** Backlog → Por hacer → En progreso → En revisión → Terminado
- **Puntos:** esfuerzo relativo (1 = muy fácil, 2 = fácil, 3 = medio, 5 = grande)
- **Responsables:** Integrante A, B, C y D se reemplazan por los nombres reales. Si el equipo es de 2, A también toma lo de C y B lo de D.
- **Meta actual:** Sprint 0 + Sprint 1 = **mitad del proyecto** para el **jueves 5 nov 2026**. Entrega final: 12 nov 2026 (por confirmar).
- Cada tarea de código corresponde a archivos ya programados y probados (ver `docs/PLAN.md` §2).

| Sprint | Puntos | % del total |
|---|---|---|
| Sprint 0 — Planeación | 11 | 15.1 % |
| **Sprint 1 — Núcleo (mitad)** | 33 | 45.2 % |
| Sprint 2 — Gutenberg, visualización e inspector completo | 16 | 21.9 % |
| Sprint 3 — Evidencias y entrega final | 13 | 17.8 % |
| **Total** | **73** | 100 % |

---

## Sprint 0 — Planeación (mar 3 nov)
**Objetivo:** tener el repositorio, el tablero y las decisiones listas para el entregable de planeación.

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| P-01 | Equipo | Definir nombre del equipo, integrantes y roles Scrum | Todos | Nombre e integrantes en el README | 1 | Por hacer |
| P-02 | Repositorio | Crear repo público con `.gitignore`, `requirements.txt` y README inicial | A | URL del repo funcionando | 1 | Por hacer |
| P-03 | Tablero | Crear GitHub Projects con las 5 columnas, cargar el backlog como issues y subir `docs/BACKLOG.md` | A | URL del tablero con todas las tareas | 2 | Por hacer |
| P-04 | Reunión de arranque | Reunión para revisar el plan y repartir bloques; acta en `docs/reuniones/` | Todos | Acta con decisiones y asistentes | 1 | Por hacer |
| P-05 | Tecnología y requisitos | Subir `docs/INSTRUCCIONES.md` y `docs/PLAN.md` (stack, arquitectura, Scrum) | B | Documentos aprobados en un PR | 1 | Por hacer |
| P-06 | Formato propio | Revisar y aprobar la extensión `.hfa` y su estructura (PLAN §4) | C | Comentario de aprobación en el PR de P-05 | 2 | Por hacer |
| P-07 | Boceto | Revisar y aprobar el boceto de la interfaz (PLAN §6) | D | Comentario de aprobación en el PR de P-05 | 1 | Por hacer |
| P-08 | Entregable de planeación | Reunir los 9 puntos que pide la actividad y entregarlos | A | Entregable enviado al profesor | 1 | Por hacer |
| P-09 | Sección 13 y MST | Preguntar al profesor por la sección 13 que falta y si sigue el árbol de expansión mínima de la Act. 5 | A | Respuesta anotada en la tarjeta | 1 | Por hacer |

---

## Sprint 1 — Núcleo Huffman: la mitad del proyecto (mar 3 nov – jue 5 nov)
**Objetivo:** subir un `.txt` → ver frecuencias y códigos → comprimir a `.hfa` con métricas → inspeccionar el `.hfa` → descomprimir → verificar que es idéntico. Todo publicado en una URL.

### Algoritmo

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| B1-01 | Frecuencias | `huffman/frecuencias.py`: `contar_frecuencias(datos)` cuenta cada byte | A | `{byte: frecuencia}` ordenado por símbolo | 1 | Por hacer |
| B2-01 | Cola de prioridad y árbol voraz | `huffman/arbol.py`: clase `Nodo` y `construir_arbol` con `heapq`, uniendo siempre los dos menores; empates deterministas; registro opcional de cada unión para la visualización | B | Mismo árbol siempre para la misma tabla | 3 | Por hacer |
| B3-01 | Códigos | `huffman/codigos.py`: `generar_codigos(raiz)`; izquierda = 0, derecha = 1; un solo símbolo = "0" | B | `{byte: "0101"}` sin códigos que sean prefijo de otros | 2 | Por hacer |

### Ingeniería

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| B4-01 | Empaquetado de bits | `huffman/bits.py`: `empaquetar` (bits → bytes con relleno) y `desempaquetar` | C | `desempaquetar(empaquetar(x)) == x` | 2 | Por hacer |
| B5-01 | Formato `.hfa` | `huffman/formato.py`: `escribir_hfa` y `leer_hfa` con `struct`; valida firma y versión | C | Archivo con la estructura de `docs/FORMATO.md` | 3 | Por hacer |
| B6-01 | Compresor, descompresor, integridad y métricas | `huffman/compresor.py`: `comprimir`, `descomprimir` (con SHA-256), `metricas`, `tamano_legible` | D | Recuperado idéntico y métricas completas | 3 | Por hacer |

### Interfaz y deploy

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| B10-01 | Tablas legibles | `huffman/visual.py` (v1): `simbolo_legible` y `tabla` | A | Filas listas para mostrar en pantalla | 1 | Por hacer |
| B7-01 | UI: entrada y análisis | `app.py` (v1): encabezado con el flujo, pestañas, subir `.txt`, tabla de frecuencias y tabla de códigos | A | Tablas visibles al subir un archivo | 3 | Por hacer |
| B7-02 | UI: comprimir y medir | `app.py` (v2): botón Comprimir, tarjetas de métricas y descarga del `.hfa` | D | Métricas en pantalla y `.hfa` descargable | 2 | Por hacer |
| B7-03 | UI: inspector y descompresión | `app.py` (v3): subir `.hfa`, metadatos, métricas, DESCOMPRIMIR, verificación SHA-256 y descarga del `.txt` | B | `recuperado.txt` idéntico al original | 3 | Por hacer |
| B12-01 | Deploy | Publicar en Streamlit Community Cloud (Python 3.12) | D | URL pública funcionando | 2 | Por hacer |

### Pruebas y documentación

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| B11-01 | Pruebas unitarias | `tests/test_huffman.py`: texto pequeño a mano, bits, integridad (6 casos), formato y métricas | C | `python -m unittest` → 11 pruebas OK | 3 | Por hacer |
| D-01 | README del Sprint 1 | Integrantes, URL, tecnologías, ejecución, estructura y uso de IA | B | README con esas secciones | 2 | Por hacer |
| D-02 | Documentar formato | `docs/FORMATO.md`: tabla de campos y ejemplo hexadecimal de `abracadabra` | C | Formato explicado campo por campo | 2 | Por hacer |
| R-01 | Review y retro Sprint 1 | Demo al profesor del flujo completo y retrospectiva | Todos | Acta en `docs/reuniones/2026-11-05.md` | 1 | Por hacer |

---

## Sprint 2 — Gutenberg, visualización e inspector completo (vie 6 nov – lun 9 nov)
**Objetivo:** buscar libros en Gutenberg, ver paso a paso cómo se construye el árbol y examinar la estructura completa de un `.hfa`.

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| B8-01 | Integración Gutenberg | `huffman/gutenberg.py`: `buscar` (catálogo OPDS: título, autor, tema) y `descargar(id)` | A | Lista de libros y bytes del libro elegido | 2 | Backlog |
| B7-04 | UI: buscar libro y texto corto | `app.py` (v4): opciones "Buscar en Project Gutenberg" (con botón "Usar este libro") y "Escribir un texto corto" | A | El libro o el texto entran al mismo flujo que un `.txt` | 2 | Backlog |
| B10-02 | Funciones de visualización | `huffman/visual.py` (v2): `arbol_a_dot` (árbol o bosque con resaltados), `bosque_en_paso`, `camino`, `nombre_nodo`, `bits_legibles` + `tests/test_visual.py` | B | 19 pruebas OK | 3 | Backlog |
| B7-05 | UI: visualización del algoritmo | `app.py` (v5): construcción paso a paso con deslizador y cola de prioridad, gráfica frecuencia vs bits, árbol con el camino de un símbolo | B | Se ve cómo la técnica voraz arma el árbol | 3 | Backlog |
| B9-01 | UI: inspector completo | `app.py` (v6): tabla y códigos reconstruidos, árbol reconstruido y primeros bits | C | Inspector con toda la estructura del `.hfa` | 3 | Backlog |
| T-01 | Prueba con libro Gutenberg | Comprimir un libro desde la app y guardar métricas y capturas en `evidencias/` | D | Tabla de resultados (≈ 43 % de reducción) | 2 | Backlog |
| R-02 | Review y retro Sprint 2 | Demo interna y retrospectiva | Todos | Acta en `docs/reuniones/` | 1 | Backlog |

---

## Sprint 3 — Evidencias y entrega final (mar 10 nov – jue 12 nov)
**Objetivo:** dejar evidencias, documentación y reporte completos, y ensayar la prueba en vivo.

| ID | Tarea | Qué se hará | Responsable | Resultado esperado | Pts | Estado |
|---|---|---|---|---|---|---|
| T-02 | Prueba con archivo nuevo | Usar un `.txt` que nunca se usó en el desarrollo | B | Evidencia en `evidencias/` | 1 | Backlog |
| T-03 | Evidencias de integridad | Capturas de SHA-256 original vs recuperado y salida de `python -m unittest` | C | Carpeta `evidencias/` completa | 2 | Backlog |
| D-03 | README completo | Descripción del algoritmo, resultados, pruebas, limitaciones y uso de IA | D | README con todo lo de INSTRUCCIONES §2.10 | 3 | Backlog |
| D-04 | Reporte técnico PDF | Reporte breve según la Guía de Reportes | Todos | PDF entregado | 5 | Backlog |
| D-05 | Ensayo de prueba en vivo | Cada integrante explica su bloque y se prueba con un archivo sorpresa | Todos | Equipo listo para la revisión | 1 | Backlog |
| R-03 | Entrega final | Enviar los 6 puntos de la entrega final | A | Entrega enviada | 1 | Backlog |

---

## Pendientes por confirmar (fuera de los sprints)

| ID | Tarea | Motivo | Estado |
|---|---|---|---|
| X-01 | Árbol de expansión mínima (Prim/Kruskal) | Lo pedía la Act. 5; no se sabe si sigue vigente (ver P-09) | Backlog |
| X-02 | Extras de visualización (animar la construcción del árbol, gráfica de frecuencias) | Solo si sobra tiempo al terminar lo obligatorio | Backlog |
