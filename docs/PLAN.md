# Plan de desarrollo — Huffman Web Compressor

Este documento explica **cómo** se construye el proyecto: tecnologías, arquitectura por bloques, formato de archivo, flujo de trabajo en GitHub y organización Scrum.
Los requisitos y la matriz de cumplimiento están en `docs/INSTRUCCIONES.md`, y las tareas en `docs/BACKLOG.md`.

> **Estado del plan:** todo el código de todos los sprints se programó y se probó el 3 nov 2026 (ver §2). El reparto por bloques está hecho para que ningún archivo entregado necesite corregirse después.

---

## 1. Tecnologías elegidas

| Pieza | Tecnología | Por qué |
|---|---|---|
| Lenguaje | **Python 3.12** | Es el lenguaje que pedía la Act. 5 y el que mejor conoce el equipo. |
| Interfaz web | **Streamlit 1.66.1** | La interfaz se escribe en Python, sin HTML ni JavaScript. Trae subida y descarga de archivos, tablas, métricas y dibujo de grafos. |
| Huffman | **Solo biblioteca estándar**: `heapq` (cola de prioridad), `struct` (encabezado binario), `hashlib` (SHA-256) | Cumple la regla de implementar Huffman nosotros, sin bibliotecas de compresión. |
| Búsqueda en Gutenberg | **Catálogo oficial OPDS** (`https://www.gutenberg.org/ebooks/search.opds/?query=...`), leído con `xml.etree` (biblioteca estándar) | Es oficial, gratuito y sin registro. Una sola búsqueda cubre título, autor y tema. |
| Descarga del libro | `https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt` con **requests 2.34.2** | Texto plano oficial de Gutenberg. |
| Árbol visual | `st.graphviz_chart` con texto DOT | Streamlit dibuja el grafo en el navegador, sin instalar Graphviz en el servidor. |
| Pruebas | `unittest` (biblioteca estándar) | No agrega dependencias. |
| Hosting | **Streamlit Community Cloud** | Gratis, despliega directo desde un repositorio público de GitHub y da una URL pública. |
| Gestión | GitHub + GitHub Projects | Lo pide la actividad. |

**Dependencias (`requirements.txt`):** `streamlit==1.66.1` y `requests==2.34.2`. Nada más.

### 1.1 Alternativas descartadas
- **API Gutendex:** era la primera opción, pero en las pruebas varias búsquedas tardaron más de 40 s o no respondieron. El catálogo oficial respondió siempre en menos de 1 s.
- **Página estática en JavaScript (GitHub Pages):** el navegador no puede descargar libros de gutenberg.org directamente por CORS. Haría falta un proxy.
- **Flask/FastAPI + HTML en Render:** funciona, pero obliga a escribir backend, frontend y endpoints. Es más código que explicar.
- **PythonAnywhere (plan gratuito):** limita las salidas a internet a una lista de sitios permitidos.

### 1.2 Proyectos de referencia de la comunidad
- [stevehjohn/Huffman](https://github.com/stevehjohn/Huffman): Huffman en C# con libros de Gutenberg. Sus archivos comprimidos quedan en ~55–58 % del original (≈ 43 % de reducción), igual que los nuestros.
- [lluiscamino/HuffmanFileCompressor](https://github.com/lluiscamino/HuffmanFileCompressor): compresor con GUI y visualización del árbol.
- [kglikith/huffman-and-lzw-compression-visualization](https://github.com/kglikith/huffman-and-lzw-compression-visualization): visualización web del árbol.
- [geekyharsh05/Huffman-Encoder](https://github.com/geekyharsh05/Huffman-Encoder): Huffman en Python con dibujo del árbol usando Graphviz.

De estos proyectos tomamos dos ideas: usar una cola de prioridad (`heapq`) y guardar la tabla de frecuencias en el encabezado para reconstruir el árbol.

---

## 2. Verificación realizada (3 nov 2026)

**Entorno:** Python 3.12.10, Git 2.55, GitHub CLI 2.102, Streamlit 1.66.1 y requests 2.34.2 en `.venv`.
**Cuidado en Windows:** Streamlit falla al instalarse si la ruta del proyecto es muy larga. Hay que clonar el repo en una ruta corta, por ejemplo `C:\Users\<usuario>\Huffman`.

**Pruebas unitarias:** `python -m unittest` → **11 pruebas OK**: texto pequeño a mano, empaquetado de bits, 6 casos de integridad (vacío, un símbolo, acentos, `\r\n`, Latin-1, los 256 bytes), detección de archivo dañado, campos del encabezado, que no se guarde el texto original, archivo inválido y métricas. Con la visualización (Sprint 2) son **19 pruebas OK**: pasos de construcción de "abracadabra", que la cola mostrada coincida con el orden real en que el algoritmo saca los nodos, el camino de un símbolo, el DOT del árbol y del bosque, y la vista de bits.

**Libros reales (comprimir → descomprimir → comparar):**

| Libro (id) | Original | `.hfa` | Reducción | Razón | Símbolos | Comprimir | Descomprimir | Idéntico |
|---|---|---|---|---|---|---|---|---|
| Don Quijote (2000) | 2,225,803 B | 1,270,569 B | 42.92 % | 1.75 | 114 | 0.67 s | 0.96 s | ✅ |
| Frankenstein (84) | 448,885 B | 254,931 B | 43.21 % | 1.76 | 97 | 0.13 s | 0.18 s | ✅ |
| Treasure Island (120), Moby Dick (2701), Monte-Cristo FR (17989) | — | — | — | — | — | — | — | ✅ |

**Interfaz en el navegador:** se probaron subir `.txt` → tablas → comprimir → métricas → descargar `.hfa` → inspector → DESCOMPRIMIR → integridad ✔ → descargar `.txt`, y también buscar en Gutenberg → usar libro. La visualización se probó con "abracadabra" (4 pasos y camino `b → 110`) y con el Quijote (113 pasos, menos de 2 s por actualización). El `.txt` descargado tiene el **mismo SHA-256** que el libro original. Un archivo falso se rechaza con un mensaje claro.

---

## 3. Decisiones de diseño

1. **Símbolo = byte (0–255).** El archivo se lee como bytes, no como texto. Así cualquier `.txt` (UTF-8, Latin-1, saltos de Windows o Linux) se recupera **byte a byte idéntico**, incluido el que lleve el profesor. En pantalla, un byte imprimible se muestra como su carácter; los demás con su nombre (`\n (salto)`) o en hexadecimal (`0xC3`).
2. **Se guarda la tabla de frecuencias, no el árbol.** El descompresor vuelve a construir el árbol con el mismo procedimiento.
3. **Árbol determinista:** las hojas entran ordenadas por símbolo. En la cola cada elemento es `(frecuencia, orden_de_llegada, nodo)`, así los empates se resuelven siempre igual. El primer nodo que sale va a la izquierda (`0`).
4. **Casos borde:** archivo vacío → 0 símbolos y 0 bits. Un solo símbolo distinto → código `"0"`.
5. **Integridad:** SHA-256 del original en el encabezado, comparado al descomprimir.
6. **Unidades:** 1 KB = 1024 B. El tamaño comprimido es el del `.hfa` completo (encabezado + datos).

---

## 4. Formato `.hfa`
Documentado campo por campo, con un ejemplo hexadecimal completo, en **`docs/FORMATO.md`**.
Resumen: `HUFA` | versión | tamaño original | total de bits | bits del último byte | SHA-256 | nombre | tabla de frecuencias | datos. Encabezado = 58 + N + 5·S bytes.

---

## 5. Arquitectura por bloques

```
Huffman/
├── app.py                  # B7/B9 Interfaz Streamlit (punto de entrada)
├── huffman/
│   ├── __init__.py
│   ├── frecuencias.py      # B1  contar_frecuencias
│   ├── arbol.py            # B2  Nodo, construir_arbol (heapq)
│   ├── codigos.py          # B3  generar_codigos
│   ├── bits.py             # B4  empaquetar, desempaquetar
│   ├── formato.py          # B5  escribir_hfa, leer_hfa
│   ├── compresor.py        # B6  comprimir, descomprimir, metricas, tamano_legible
│   ├── visual.py           # B10 tablas (S1) · árbol, paso a paso, camino, bits (S2)
│   └── gutenberg.py        # B8  buscar, descargar (S2)
├── tests/
│   ├── __init__.py
│   ├── test_huffman.py     # B11 pruebas del núcleo (S1)
│   └── test_visual.py      # B11 pruebas de la visualización (S2)
├── docs/  (INSTRUCCIONES, PLAN, BACKLOG, FORMATO, reuniones/)
├── evidencias/             # capturas y resultados (Sprint 3)
├── requirements.txt
├── README.md
└── .gitignore
```

### 5.1 Contrato de cada bloque

| Bloque | Función(es) | Entrada → Salida | Usa |
|---|---|---|---|
| B1 | `contar_frecuencias(datos)` | `bytes` → `{byte: frecuencia}` | — |
| B2 | `Nodo`, `construir_arbol(frecuencias)` | dict → raíz `Nodo` (o `None`) | — |
| B3 | `generar_codigos(raiz)` | `Nodo` → `{byte: "0101"}` | B2 |
| B4 | `empaquetar(bits)`, `desempaquetar(datos, total_bits)` | `"0101"` ↔ `bytes` + bits del último byte | — |
| B5 | `escribir_hfa(...)`, `leer_hfa(contenido)` | campos ↔ `bytes` del `.hfa` | — |
| B6 | `comprimir`, `descomprimir`, `metricas`, `tamano_legible` | `bytes` ↔ `.hfa`; métricas | B1–B5 |
| B10 | `simbolo_legible`, `tabla` (S1) · `nombre_nodo`, `arbol_a_dot`, `bosque_en_paso`, `camino`, `bits_legibles` (S2) | datos → filas; árbol o bosque → DOT con resaltados; pasos → cola en el paso k; código → nodos del camino | B2 |
| B8 | `buscar(texto)`, `descargar(id)` | texto → libros; id → `bytes` | — |
| B7/B9 | `app.py`: una función por sección | interfaz | todos |

### 5.2 Secciones de la interfaz (`app.py`)

| Sección | Función | Sprint |
|---|---|---|
| Encabezado con el flujo y pestañas | (final del archivo) | 1 |
| 1. Entrada: subir `.txt` | `seccion_entrada` | 1 |
| 1. Entrada: buscar en Gutenberg o escribir un texto corto | `seccion_entrada` (se agrega) | 2 |
| 2. Analizar: tabla de frecuencias | `seccion_analisis` | 1 |
| 3. Construir Huffman: tabla de códigos | `seccion_huffman` | 1 |
| 3.1 Construcción paso a paso: deslizador, cola de prioridad y unión resaltada | `seccion_huffman` (se agrega) | 2 |
| 3.2 Códigos con gráfica frecuencia vs bits | `seccion_huffman` (se agrega) | 2 |
| 3.3 Árbol con el camino de un símbolo resaltado | `seccion_huffman` (se agrega) | 2 |
| 4. Comprimir y medir + descarga | `seccion_comprimir`, `mostrar_metricas` | 1 |
| 5. Inspector: metadatos + métricas | `seccion_inspector` | 1 |
| 5. Inspector: tabla, árbol y bits reconstruidos | `seccion_inspector` (se agrega) | 2 |
| 6. Descomprimir, verificar y descargar | `seccion_inspector` | 1 |

### 5.3 Flujo de datos
```
.txt / Gutenberg ──► B1 frecuencias ──► B2 árbol ──► B3 códigos
                                                       │
                     B6 comprimir ◄── B4 empaquetar ◄──┘
                         │
                         ▼
                  B5 escribir .hfa ──► descarga
                                           │
   .hfa subido ──► B5 leer ──► INSPECTOR (metadatos, tabla, códigos, árbol, bits)
                                  │  [botón DESCOMPRIMIR]
                                  ▼
                 B2 árbol ──► B4 desempaquetar ──► decodificar ──► SHA-256 ✔ ──► recuperado.txt
```

---

## 6. Boceto de la aplicación

```
┌───────────────────────────────────────────────────────────────┐
│  HUFFMAN WEB COMPRESSOR                                       │
│  SUBIR/BUSCAR → ANALIZAR → HUFFMAN → COMPRIMIR → INSPECCIONAR │
│  → DESCOMPRIMIR → VERIFICAR                                   │
├───────────────────────────────────────────────────────────────┤
│ [ Pestaña: Comprimir ]   [ Pestaña: Inspector / Descomprimir ]│
├───────────────────────────────────────────────────────────────┤
│ 1. ENTRADA (•) Subir .txt ( ) Gutenberg ( ) Escribir texto    │
│              [ Examinar... ]   /  [ quijote ] [Buscar]        │
│                                   > Don Quijote (#2000) [Usar]│
│ 2. ANALIZAR  | Símbolo | Byte | Frecuencia | % |              │
│ 3. HUFFMAN                                                    │
│  3.1 Paso a paso  Paso [====o-----] 2 de 4                    │
│      "Salen [b: 2] y [r: 2] → nuevo nodo 4"                   │
│      Cola: (2) · (4) · [a: 5]                                 │
│         (2)        (4)*      [a 5]     * = unión del paso     │
│        /   \      /   \                                       │
│      [c 1][d 1] [b 2][r 2]                                    │
│  3.2 Códigos  | tabla con Código y Bits |  gráfica de barras  │
│  3.3 Árbol    Resaltar: [ b → 110 ]                           │
│      Raíz (11) —1→ (6) —1→ (4) —0→ [b: 2] = 110 (en rojo)     │
│ 4. COMPRIMIR [Comprimir]                                      │
│   Original 2.12 MB | Comprimido 1.21 MB | Ahorro 932.84 KB    │
│   Reducción 42.92 % | Razón 1.75 : 1 | Símbolos 114           │
│   [ Descargar pg2000.hfa ]                                    │
├───────────────────────────────────────────────────────────────┤
│ 5. INSPECTOR [ Subir .hfa ]                                   │
│   Metadatos: archivo, extensión, HUFA v1, nombre original,    │
│   total de bits, bits del último byte, encabezado, SHA-256    │
│   Métricas · tabla y códigos reconstruidos · ▸ árbol          │
│   Primeros bits: 10001010 11110100 10010110 ...               │
│ 6. [ DESCOMPRIMIR ]  OK Integridad verificada (SHA-256)       │
│   Texto recuperado (vista previa)  [ Descargar .txt ]         │
└───────────────────────────────────────────────────────────────┘
```

---

## 7. Organización Scrum

### 7.1 Roles

| Rol | Quién | Qué hace |
|---|---|---|
| Product Owner | Profesor (cliente) / representante del equipo | Define prioridades y acepta entregas. |
| Scrum Master | Integrante A | Mantiene el tablero al día, organiza reuniones y quita bloqueos. |
| Equipo de desarrollo | Todos | Suben, revisan y explican sus bloques. |

### 7.2 Sprints

| Sprint | Fechas | Objetivo | Revisión |
|---|---|---|---|
| Sprint 0 | mar 3 nov | Planeación: repo, tablero, decisiones, formato, boceto | jue 5 nov |
| **Sprint 1** | mar 3 – jue 5 nov | **Mitad del proyecto:** núcleo Huffman + `.hfa` + comprimir/descomprimir + métricas + inspector básico + deploy | **jue 5 nov** |
| Sprint 2 | vie 6 – lun 9 nov | Gutenberg + árbol visual + inspector completo | lun 9 nov (interna) |
| Sprint 3 | mar 10 – jue 12 nov | Evidencias de pruebas, README completo, reporte PDF | **jue 12 nov** (final, por confirmar) |

> La planeación debía empezar el 29 oct, pero empezó el 3 nov. En el tablero se registra la fecha real.

### 7.3 Eventos
- **Sprint Planning** (inicio de sprint): se eligen tareas y responsables.
- **Daily** (breve, por chat): qué hice, qué haré y qué me bloquea.
- **Sprint Review** (cada jueves con el profesor): se presenta lo que está en *Terminado*.
- **Retrospectiva** (10 min después de la review).
- Cada reunión deja un acta en `docs/reuniones/AAAA-MM-DD.md`.

### 7.4 Definición de Terminado (DoD)

1. El código está en `main` mediante un Pull Request, revisado por otro integrante o, si nadie está disponible, con un comentario de autorrevisión.
2. `python -m unittest` pasa.
3. Tiene comentarios en español y su documentación.
4. El responsable puede explicarlo.

---

## 8. Flujo de trabajo en GitHub

1. Cada tarea del backlog es un **Issue** dentro de **GitHub Projects**.
2. Al empezar: tarjeta a **En progreso** y rama `b1-frecuencias`, `b2-arbol`, etc.
3. Commit desde **su propia cuenta**, con el mensaje de su ficha.
4. **Pull Request** con `Closes #N` → tarjeta a **En revisión**.
5. Otro integrante revisa (si no hay nadie disponible, el autor deja un comentario de autorrevisión) → **Merge pull request** → **Terminado**. `main` no tiene reglas que bloqueen; usar siempre rama + PR es un acuerdo del equipo.
6. **`app.py` y `visual.py` los editan varias personas:** cada quien sube la versión completa de su ficha **en el orden indicado**, después del merge de la ficha anterior. Así nadie borra el trabajo de otro.

Las fichas con archivos, ramas, commits y movimientos del tablero están en `para_el_equipo/ENTREGAS.md` (no se sube al repo).

---

## 9. Ejecución local
```bash
git clone https://github.com/Souls-Nao/huffman-web-compressor.git C:\Users\<usuario>\Huffman
cd C:\Users\<usuario>\Huffman
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m unittest
streamlit run app.py
```

## 10. Despliegue (Streamlit Community Cloud)

1. El repositorio debe ser **público**, con `app.py` y `requirements.txt` en la raíz.
2. Entrar a `share.streamlit.io` con la cuenta de GitHub → **Create app** → repo, rama `main`, archivo `app.py`. En **Advanced settings**, elegir Python **3.12**.
3. Copiar la URL pública al `README.md`.
4. Cada merge a `main` vuelve a desplegar la app automáticamente.

---

## 11. Riesgos

| Riesgo | Mitigación |
|---|---|
| gutenberg.org lento o caído durante la revisión | Mensaje de error claro. Siempre queda la opción de subir un `.txt` local. |
| Archivo muy grande (> 20 MB) | Límite documentado; los libros de Gutenberg pesan entre 0.2 y 5 MB. |
| Árbol de > 200 nodos difícil de leer | Se muestra en un desplegable con pantalla completa; la tabla de códigos es la referencia principal. |
| Un integrante sube un `app.py` viejo y borra cambios | Orden obligatorio de fichas y revisión del PR. |
| Integrantes sin actividad en el historial | Cada ficha tiene responsable fijo, que la sube él mismo. |
