# Formato de archivo `.hfa` (versión 1)

`.hfa` (*Huffman File Archive*) es el formato propio del proyecto. Guarda lo necesario para reconstruir el archivo original **sin el `.txt`**: la tabla de frecuencias (para rehacer el árbol) y los bits de Huffman empaquetados en bytes.
**El texto original no se guarda.**

Código: `huffman/formato.py`. Todos los enteros son **sin signo, little-endian** (el byte menos significativo va primero).

## 1. Estructura

| # | Campo | Tamaño | `struct` | Descripción |
|---|---|---|---|---|
| 1 | Firma | 4 B | `4s` | Siempre `HUFA` (`48 55 46 41`). Identifica el formato. |
| 2 | Versión | 1 B | `B` | `1` |
| 3 | Tamaño original | 8 B | `Q` | Bytes del archivo original. |
| 4 | Total de bits | 8 B | `Q` | Cantidad de bits válidos de los datos comprimidos. |
| 5 | Bits válidos del último byte | 1 B | `B` | 1–8 (0 si no hay datos). Los demás bits del último byte son relleno (`0`). |
| 6 | SHA-256 del original | 32 B | `32s` | Huella del original para verificar la integridad. |
| 7 | Largo del nombre (N) | 2 B | `H` | Bytes del nombre original en UTF-8. |
| 8 | Nombre original | N B | — | Metadato, por ejemplo `quijote.txt`. |
| 9 | Número de símbolos (S) | 2 B | `H` | 0–256 |
| 10 | Tabla de frecuencias | 5·S B | `B` + `I` | Por cada símbolo: el byte (1 B) y su frecuencia (4 B), ordenada por símbolo. |
| 11 | Datos comprimidos | resto | — | Bits de Huffman agrupados de 8 en 8, de izquierda a derecha. |

- **Tamaño del encabezado:** 58 + N + 5·S bytes.
- **Tamaño total del `.hfa`:** encabezado + ⌈total de bits / 8⌉.

## 2. Cómo se lee (descompresión)

1. Verificar que la firma sea `HUFA` y la versión `1`. Si no, el archivo se rechaza.
2. Leer los campos 3 a 10 en orden.
3. Con la tabla de frecuencias, construir el árbol con el mismo algoritmo voraz que al comprimir (`huffman/arbol.py`). El árbol sale idéntico porque los empates se resuelven siempre igual.
4. Convertir los datos a bits y quedarse solo con los primeros `total de bits` (se descarta el relleno).
5. Recorrer el árbol bit por bit (0 = izquierda, 1 = derecha). Cada hoja alcanzada es un byte del original.
6. Calcular el SHA-256 del resultado y compararlo con el campo 6. Si son iguales, el archivo es **idéntico** al original.

## 3. Ejemplo completo: `abracadabra`

Archivo original `abra.txt` = `abracadabra` (11 bytes).

**Frecuencias y códigos** (comprobables a mano, ver `tests/test_huffman.py`):

| Símbolo | Byte | Frecuencia | Código |
|---|---|---|---|
| a | 0x61 | 5 | `0` |
| b | 0x62 | 2 | `110` |
| c | 0x63 | 1 | `100` |
| d | 0x64 | 1 | `101` |
| r | 0x72 | 2 | `111` |

Construcción voraz: c(1) + d(1) = 2 → b(2) + r(2) = 4 → nodo cd(2) + nodo br(4) = 6 → a(5) + nodo(6) = 11 (raíz).

**Bits:** `0 110 111 0 100 0 101 0 110 111 0` = 23 bits → `01101110 10001010 1101110`+`0` (relleno) = `6E 8A DC`.

**Archivo `abra.hfa` completo (94 bytes):**

```
48 55 46 41                  firma "HUFA"
01                           versión 1
0B 00 00 00 00 00 00 00      tamaño original = 11
17 00 00 00 00 00 00 00      total de bits = 23
07                           bits válidos del último byte = 7
04 5B AB DC D2 11 89 60      SHA-256 de "abracadabra" (32 bytes)
E8 C8 B8 E0 EC F6 5B 73
46 86 E1 B1 8F 58 71 0C
96 46 77 9F 49 E9 42 AE
08 00                        largo del nombre = 8
61 62 72 61 2E 74 78 74      "abra.txt"
05 00                        número de símbolos = 5
61 05 00 00 00               'a' = 5
62 02 00 00 00               'b' = 2
63 01 00 00 00               'c' = 1
64 01 00 00 00               'd' = 1
72 02 00 00 00               'r' = 2
6E 8A DC                     datos comprimidos (23 bits + 1 de relleno)
```

Encabezado: 58 + 8 + 5·5 = 91 bytes. Datos: 3 bytes. Total: 94 bytes.

> En textos muy pequeños el `.hfa` pesa **más** que el original porque el encabezado ocupa más que el ahorro. En libros reales el encabezado es mínimo (≈ 640 B en un libro de 2 MB) y la reducción ronda el 43 %.

## 4. Decisiones del diseño
- **Tabla de frecuencias en lugar del árbol:** es fácil de guardar (5 B por símbolo) y el inspector puede mostrarla directamente.
- **Símbolo = byte:** cualquier `.txt` (UTF-8, Latin-1, saltos `\r\n`) se recupera byte a byte idéntico.
- **SHA-256:** detecta cualquier cambio, aunque sea de un solo bit.
- **Frecuencia en 4 bytes:** permite hasta ~4,290 millones de repeticiones de un símbolo (archivos de hasta 4 GB).
