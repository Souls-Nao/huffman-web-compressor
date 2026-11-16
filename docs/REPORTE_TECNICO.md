---
title: "Huffman Web Compressor: reporte técnico"
subtitle: "Análisis de Algoritmos · 2026B"
---

# Huffman Web Compressor: reporte técnico

**Equipo:** _(nombre por definir)_ · Johan Daniel Gutierrez Nava, Oswaldo Daniel Castañeda Hernández, Cuauhtémoc Soria Hernández, Omar Alejandro Ruvalcaba Velazquez
**Repositorio:** https://github.com/Souls-Nao/huffman-web-compressor · **Fecha:** noviembre de 2026

## 1. Resumen
Se construyó una aplicación web que comprime texto con el algoritmo de Huffman y lo guarda en un formato propio, `.hfa`. La aplicación recupera el texto idéntico a partir de **solo** el archivo comprimido y lo verifica con SHA-256. Incluye búsqueda en Project Gutenberg, visualización paso a paso de la cola de prioridad, árbol interactivo con resaltado de caminos e inspector del archivo. En textos en inglés y español la reducción ronda el 41–43 %, a menos de 0.04 bits por carácter de la entropía de Shannon.

## 2. Problema y enfoque voraz
**Problema.** Dado un texto de `L` bytes sobre un alfabeto de `n ≤ 256` símbolos con frecuencias `f(s)`, encontrar un código **libre de prefijos** que minimice el costo total `C = Σ f(s)·|código(s)|`.

**Estrategia voraz.** Se mantiene una cola de prioridad con un nodo por símbolo. En cada paso se extraen los **dos nodos de menor frecuencia**, se unen en un padre con la suma y se reinsertan. Tras `n − 1` uniones queda la raíz. El código de un símbolo es el camino desde la raíz (izquierda `0`, derecha `1`).

**Por qué es correcto** (argumento de intercambio, CLRS §16.3). (1) Existe un árbol óptimo en el que los dos símbolos menos frecuentes `x, y` son hermanos en el nivel más profundo: si no lo fueran, intercambiarlos con hojas más profundas no aumenta `C`, porque cambia `f` grande por `f` pequeña en niveles más profundos. (2) Al unir `x` e `y` en un nodo `z` con `f(z) = f(x) + f(y)`, el costo del árbol original es el del reducido más `f(x) + f(y)`; por lo tanto, un óptimo del problema reducido produce un óptimo del original. Por inducción sobre `n`, la elección voraz es segura.

**Determinismo.** Las hojas entran ordenadas por símbolo y cada elemento de la cola es `(frecuencia, orden de llegada)`. Los empates se resuelven siempre igual, así que compresor y descompresor construyen **el mismo árbol** a partir de la tabla de frecuencias. Esta regla es idéntica en las versiones Python y JavaScript, lo que hace los archivos intercambiables.

## 3. Análisis de complejidad

Sea `L` el número de bytes del texto y `n` el número de símbolos distintos (`n ≤ 256`). Con `N = n` el análisis del algoritmo voraz es el clásico `O(N log N)`; el costo del archivo completo añade el recorrido del texto.

| Etapa | Tiempo | Justificación |
|---|---|---|
| Contar frecuencias | `O(L)` | Un recorrido con contador por byte. |
| Construir el árbol | **`O(n log n)`** | `n` inserciones iniciales y `n − 1` uniones; cada una hace 2 extracciones y 1 inserción de `O(log n)` en el min-heap. |
| Generar códigos | `O(n)` | Un recorrido del árbol (tiene `2n − 1` nodos). |
| Codificar y empaquetar | `O(L + bits)` | Se escribe cada código; `bits = Σ f(s)·|c(s)| ≤ L·(n − 1)`, en la práctica ≈ `4.6·L` en texto natural. |
| SHA-256 | `O(L)` | |
| **Compresión total** | **`O(L + n log n)`** | |
| Descompresión | `O(n log n + bits)` | Reconstruir el árbol y recorrerlo un bit por paso; cada hoja alcanzada emite un símbolo. |

**Espacio:** `O(n)` para el árbol y la tabla, más `O(L)` para el texto y la salida (el empaquetado escribe directo en un `Uint8Array`, sin cadena de bits intermedia).

**Observación.** Como `n ≤ 256`, el término `n log n` está acotado por una constante (≈ 2,048 operaciones de heap) y el costo real del programa es **lineal en `L`**. El factor logarítmico es el que cuenta si el alfabeto crece (por ejemplo, palabras como símbolos).

**Medición** (`npm run evidencias`, ver `evidencias/RESULTADOS.md`):

| n (símbolos) | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 |
|---|---|---|---|---|---|---|---|---|
| n·log₂n | 2 | 8 | 24 | 64 | 160 | 384 | 896 | 2,048 |
| µs por árbol | 2.1 | 2.2 | 1.0 | 1.6 | 3.7 | 8.0 | 18.2 | 38.1 |

Al duplicar `n` de 64 a 128 y de 128 a 256 el tiempo se multiplica por ≈ 2.3 y ≈ 2.1: crecimiento casi lineal con un factor logarítmico leve y no cuadrático (que daría ×4). Para valores pequeños de `n` domina el costo fijo de crear objetos. Con `n` fijo, el pipeline completo mide ≈ 30 ns por byte para `L` desde 35 KB hasta 562 KB: tiempo lineal en `L`.

## 4. Formato `.hfa` (versión 1)
Enteros sin signo, **little-endian**. Se guarda la **tabla de frecuencias** (no el árbol): 5 bytes por símbolo bastan para reconstruir el mismo árbol. **El texto original no se guarda.**

| # | Campo | Bytes | Descripción |
|---|---|---|---|
| 1 | Firma | 4 | `HUFA` |
| 2 | Versión | 1 | `1` |
| 3 | Tamaño original | 8 | bytes del archivo original |
| 4 | Total de bits | 8 | bits válidos de los datos |
| 5 | Bits válidos del último byte | 1 | 1–8 (0 si no hay datos); el resto es relleno de ceros |
| 6 | SHA-256 del original | 32 | verificación de integridad |
| 7 | Largo del nombre `N` | 2 | |
| 8 | Nombre original | `N` | UTF-8 |
| 9 | Número de símbolos `S` | 2 | 0–256 |
| 10 | Tabla de frecuencias | `5·S` | por símbolo: byte (1) + frecuencia (4) |
| 11 | Datos comprimidos | resto | bits de Huffman de 8 en 8, de izquierda a derecha |

Tamaño del encabezado: `58 + N + 5·S`. Tamaño total: encabezado + `⌈bits / 8⌉`.

**Ejemplo `abracadabra`** (11 B → 94 B): códigos `a=0, b=110, c=100, d=101, r=111`; 23 bits → datos `6E 8A DC` (el último byte usa 7 bits). El encabezado ocupa 91 B, por eso un texto tan corto crece.

**Validaciones al leer.** Firma y versión; suma de frecuencias = tamaño original; `bits ≥ tamaño original` (cada símbolo usa al menos 1 bit); `bytes de datos = ⌈bits/8⌉`; bits del último byte coherentes. Un archivo truncado o con encabezado alterado se rechaza con un mensaje claro; uno con datos alterados se detecta con el SHA-256.

## 5. Arquitectura
Núcleo JavaScript puro (`core/`) sin DOM; módulos de interfaz (`input`, `steps`, `tree`, `compress`, `inspector`) con un *viewmodel* puro y una vista DOM; comunicación por un `store` publicar/suscribir. El mismo núcleo y los *viewmodels* se reutilizan en React Native (Web). Un proxy gratuito (Cloudflare Workers) resuelve el CORS de Project Gutenberg. Detalle en `docs/ARQUITECTURA_WEB.md`.

## 6. Pruebas
43 pruebas automáticas (`npm test`):

| Tipo | Qué comprueban |
|---|---|
| Unitarias | Frecuencias, códigos calculados a mano, ausencia de prefijos con 256 símbolos, casos borde (vacío, un símbolo), cola registrada = orden real de salida, camino de un símbolo, empaquetado de bits, métricas, layout |
| Formato | Ejemplo documentado byte a byte (94 B, `6E 8A DC`), campos del encabezado, texto original ausente, archivos inválidos/truncados/alterados |
| Integridad | Ida y vuelta con 7 casos borde y 200 entradas aleatorias reproducibles; detección de un bit cambiado |
| Integración | Original → `.hfa` → recuperado sin el original; el tamaño predicho por el análisis coincide con el `.hfa` real |
| Compatibilidad | Python comprime y JS descomprime, JS comprime y Python descomprime; **los archivos son idénticos byte a byte** |
| Módulos | Parser OPDS, búsqueda/descarga de Gutenberg con `fetch` simulado, reglas del proxy, *viewmodels* del árbol, la cola y el inspector |

Además se recorrió el flujo completo en un navegador real (Chromium) sin errores de consola.

## 7. Rendimiento y resultados

| Texto | Original | `.hfa` | Reducción | Razón | Símbolos | Comprimir | Descomprimir | SHA-256 |
|---|---|---|---|---|---|---|---|---|
| GPL-3 | 35,149 B | 20,699 B | 41.11 % | 1.70 | 76 | 1.5 ms | 1.3 ms | ✅ |
| Apache-2.0 | 11,358 B | 6,770 B | 40.39 % | 1.68 | 76 | 0.5 ms | 0.4 ms | ✅ |
| GFDL-1.3 | 22,955 B | 13,576 B | 40.86 % | 1.69 | 76 | 0.9 ms | 0.7 ms | ✅ |
| Don Quijote (#2000)* | 2,225,803 B | 1,270,569 B | 42.92 % | 1.75 | 114 | 0.67 s* | 0.96 s* | ✅ |
| Frankenstein (#84)* | 448,885 B | 254,931 B | 43.21 % | 1.76 | 97 | 0.13 s* | 0.18 s* | ✅ |

\* Mediciones del equipo con la versión Python (`docs/PLAN.md` §2). Las tres primeras filas son de la versión JavaScript.

**Cercanía a la entropía.** Huffman asigna `L̄ = bits / L` bits por carácter; el límite teórico es la entropía de Shannon `H`. Siempre `H ≤ L̄ < H + 1`:

| Texto | H (bits/car.) | L̄ Huffman | Diferencia |
|---|---|---|---|
| GPL-3 | 4.5733 | 4.6094 | 0.036 |
| Apache-2.0 | 4.4267 | 4.4512 | 0.025 |
| GFDL-1.3 | 4.5459 | 4.5751 | 0.029 |

Huffman es óptimo **entre códigos símbolo a símbolo**; no aprovecha el contexto (pares de letras, palabras repetidas), que es lo que explotan compresores como LZ77/DEFLATE y por eso comprimen más.

## 8. Limitaciones
Encabezado fijo pesado en textos cortos; archivos completos en memoria (≈ 20 MB recomendados); búsqueda de Gutenberg limitada a 25 resultados y dependiente de un proxy; frecuencias de 4 bytes (archivos hasta 4 GB); un solo paso sobre el texto para contar y otro para codificar (no hay compresión adaptativa). El análisis de la búsqueda en Gutenberg se probó con una muestra del catálogo OPDS y simulaciones de red; falta la comprobación contra el sitio en vivo desde el despliegue.

## 9. Uso de IA
Claude (Anthropic) asistió en el port a JavaScript, la interfaz modular, las pruebas y borradores de documentación. El equipo revisó y ejecutó todo el código y puede explicarlo.

## 10. Conclusiones
La técnica voraz con cola de prioridad produce un código óptimo con costo `O(n log n)` sobre el alfabeto y `O(L)` sobre el texto. El formato `.hfa` es compacto, verificable y compatible entre implementaciones. La visualización paso a paso y el resaltado de caminos hacen explícito por qué los símbolos frecuentes reciben códigos cortos.

## Referencias
1. D. A. Huffman, «A Method for the Construction of Minimum-Redundancy Codes», *Proceedings of the IRE*, 40(9), 1952.
2. T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein, *Introduction to Algorithms*, cap. 16.3 «Huffman codes».
3. C. E. Shannon, «A Mathematical Theory of Communication», 1948.
4. Project Gutenberg, catálogo OPDS: https://www.gutenberg.org
