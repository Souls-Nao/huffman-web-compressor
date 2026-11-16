# Presentación final: estructura y guion

**Duración sugerida:** 15 min (11 de exposición + 4 de prueba en vivo y preguntas) · **Reparto:** cada integrante explica su bloque (D-05).
**Antes de empezar:** app abierta en la pestaña de entrada, un `.txt` de Gutenberg ya descargado como respaldo, y un `.hfa` generado de antemano por si falla la red.

| # | Diapositiva | Quién | Min |
|---|---|---|---|
| 1 | Portada y problema | Dev1 | 0:45 |
| 2 | La idea voraz | Dev2 | 1:30 |
| 3 | Cola de prioridad paso a paso (demo) | Dev3 | 1:30 |
| 4 | Del árbol a los códigos | Dev2 | 1:00 |
| 5 | Bits reales y formato `.hfa` | Dev4 | 1:30 |
| 6 | Integridad: SHA-256 | Dev4 | 0:45 |
| 7 | Arquitectura y Gutenberg | Dev1 | 1:15 |
| 8 | Inspector (demo) | Dev3 | 1:00 |
| 9 | Complejidad | Dev4 | 1:15 |
| 10 | Resultados y pruebas | Dev4 | 1:00 |
| 11 | Limitaciones, IA y cierre | Dev1 | 0:30 |
| 12 | Prueba en vivo con archivo sorpresa | Todos | 3:00 |

---

## 1. Portada y problema (Dev1)
**En pantalla:** título, logo/flujo `Subir → Analizar → Huffman → Comprimir → Inspeccionar → Descomprimir → Verificar`, nombres del equipo.
**Guion:**
- Un carácter ocupa 8 bits, pero no todos aparecen igual de seguido: en español la `e` y el espacio abundan y la `q` casi no aparece.
- Si damos códigos cortos a lo frecuente y largos a lo raro, el archivo pesa menos sin perder nada.
- Huffman lo resuelve con una técnica **voraz**. Lo implementamos nosotros: sin zip, gzip ni zlib.
- Hoy mostramos el flujo completo y un formato de archivo propio, `.hfa`.

## 2. La idea voraz (Dev2)
**En pantalla:** abracadabra con frecuencias `a5 b2 r2 c1 d1`.
**Guion:**
- Regla única: **unir siempre los dos nodos de menor frecuencia**.
- Es voraz porque decide con lo que ve ahora y nunca se arrepiente. La razón es que los dos símbolos más raros pueden ir juntos en lo más profundo sin costar de más: así se demuestra que la decisión es segura.
- Resultado: un árbol cuyo código minimiza el total de bits entre los códigos símbolo a símbolo.

## 3. Cola de prioridad paso a paso (Dev3) — *demo*
**En la app:** escribir `abracadabra`, mover el deslizador.
**Guion:**
- La cola es un min-heap: siempre saca el mínimo en `O(log n)`.
- Paso 1: salen `c:1` y `d:1`; vuelve un nodo de 2. Paso 2: salen `b:2` y `r:2`… Paso 4: queda la raíz de 11.
- Las fichas naranjas son las que salen, la verde es la que entra. El bosque de abajo muestra los árboles parciales.
- Con 4 pasos para 5 símbolos: siempre `n − 1` uniones.

## 4. Del árbol a los códigos (Dev2) — *demo*
**En la app:** elegir `b` en el selector.
**Guion:**
- Izquierda es `0`, derecha es `1`. Para `b`: derecha, derecha, izquierda → `110`.
- Las letras solo están en las hojas, por eso ningún código es prefijo de otro y se puede decodificar sin separadores.
- La gráfica muestra la relación: barras altas (frecuentes) con color de código corto.

## 5. Bits reales y formato `.hfa` (Dev4)
**En pantalla:** tabla de campos del formato y el hexadecimal de `abracadabra` (94 B).
**Guion:**
- Los códigos son texto `"0110…"`; de verdad se juntan de 8 en 8 en bytes. Si sobran bits, se rellena con ceros y se **guarda cuántos bits son válidos**.
- Guardamos la **tabla de frecuencias**, no el árbol: 5 bytes por símbolo. Al descomprimir se reconstruye el mismo árbol porque los empates se resuelven siempre igual.
- Encabezado: firma `HUFA`, versión, tamaño original, total de bits, SHA-256, nombre y la tabla. **No guardamos el texto.**
- Por eso un texto de 11 bytes pesa 94: el encabezado cuesta más que el ahorro. En un libro es insignificante.

## 6. Integridad (Dev4)
**Guion:** el SHA-256 del original va en el encabezado. Al descomprimir recalculamos el hash del resultado: si coincide, el archivo es idéntico bit a bit; si alguien cambia un solo bit del archivo, la app lo detecta.

## 7. Arquitectura y Gutenberg (Dev1)
**En pantalla:** diagrama `core → módulos → store`, y `navegador → proxy → gutenberg.org`.
**Guion:**
- Núcleo JS puro sin interfaz: es el mismo que se probó contra la versión Python y produce **archivos idénticos byte a byte**.
- Cinco módulos independientes con un store compartido; cada integrante dueño de sus carpetas.
- Gutenberg no permite leerlo desde el navegador (CORS), así que usamos un proxy gratuito que solo reenvía dos rutas: búsqueda y texto plano.
- Buscar por título, autor o tema, elegir y usar el libro.

## 8. Inspector (Dev3) — *demo*
**En la app:** *Inspeccionar este archivo* → mostrar metadatos, tabla, árbol y primeros bits; luego **DESCOMPRIMIR**.
**Guion:**
- El inspector trabaja solo con el `.hfa`: nombre, versión, bits, tamaños y SHA-256.
- Tabla de bits por carácter: `a` cuesta 1 bit en lugar de 8.
- Los primeros bits aparecen separados por palabra de código, cada una con su letra.
- Solo después del botón aparece el texto, y con la verificación SHA-256.

## 9. Complejidad (Dev4)
**En pantalla:** tabla de etapas y la medición.
**Guion:**
- `n` = símbolos distintos (máximo 256), `L` = bytes del texto.
- Construir el árbol es **`O(n log n)`**: `n − 1` uniones, cada una `O(log n)` en el heap.
- Contar y codificar son `O(L)`. Total: **`O(L + n log n)`**.
- Como `n ≤ 256`, en la práctica es lineal: medimos ≈ 30 ns por byte de 35 KB a 562 KB. Al duplicar `n`, el tiempo del árbol se multiplica por ≈ 2, no por 4.

## 10. Resultados y pruebas (Dev4)
**En pantalla:** tabla de resultados y salida de `npm test`.
**Guion:**
- Reducción de 40–43 %; el Quijote pasa de 2.12 MB a 1.21 MB (42.92 %).
- Estamos a menos de 0.04 bits por carácter del límite teórico (la entropía).
- 43 pruebas automáticas: ejemplo a mano, casos borde, 200 casos aleatorios, archivos dañados y compatibilidad con Python en ambos sentidos.

## 11. Limitaciones, IA y cierre (Dev1)
- Textos muy cortos pesan más; se recomiendan archivos de hasta ~20 MB; Gutenberg depende de un proxy.
- Usamos Claude como asistente; revisamos, ejecutamos las pruebas y podemos explicar todo el código.
- Huffman es óptimo símbolo a símbolo; compresores con contexto (LZ77/DEFLATE) comprimen más.

## 12. Prueba en vivo con archivo sorpresa (todos)
Guion de seguridad, en orden:
1. Subir el `.txt` del profesor → ver frecuencias y árbol (Dev2 resalta una letra que él elija).
2. **Comprimir** → leer reducción, razón y símbolos (Dev1).
3. **Inspeccionar** el `.hfa` (Dev3) → **DESCOMPRIMIR** → mostrar *Integridad verificada* y comparar el hash (Dev4).
4. Si falla la red: usar el libro y el `.hfa` de respaldo. Si el archivo no es UTF-8, no pasa nada: el símbolo es el byte.

---

## Preguntas probables
| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué es voraz y no programación dinámica? | La elección local (los dos menores) es siempre parte de una solución óptima; no hace falta explorar alternativas. |
| ¿Por qué guardan frecuencias y no el árbol? | Son 5 B por símbolo y el árbol se reconstruye idéntico por el desempate determinista. |
| ¿Qué pasa con un archivo de un solo símbolo? | El árbol es una hoja; se asigna el código `0` (1 bit por símbolo). |
| ¿Por qué el `.hfa` pesa más en textos pequeños? | El encabezado mínimo son 58 B + nombre + 5 B por símbolo. |
| ¿Cómo saben que el recuperado es idéntico? | SHA-256 guardado en el encabezado, recalculado al descomprimir. |
| ¿Es mejor que ZIP? | No: ZIP usa además repeticiones (LZ77). Huffman solo usa frecuencias; por eso se combina en DEFLATE. |
| ¿Es `O(N log N)`? | El árbol sí, con N = símbolos distintos; el archivo completo es `O(L + n log n)`. |
