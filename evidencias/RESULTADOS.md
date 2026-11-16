# Resultados y evidencias (generado automáticamente)

Generado con `npm run evidencias` el 2026-11-08 con Node v22.23.4. No editar a mano: se vuelve a generar.

## 1. Pruebas automáticas
- tests 43
- pass 43
- fail 0
- skipped 0

```
✔ opds: lista libros, decodifica entidades y descarta navegacion y repetidos
✔ gutenberg.buscar: arma la URL y limita resultados
✔ gutenberg.descargar: bytes, progreso y errores claros
✔ proxy: solo reenvia las dos rutas permitidas y agrega CORS
✔ vista desde el texto actual: tamano final exacto y bits por caracter
✔ vista desde el .hfa: metadatos y misma tabla, sin el texto original
✔ bits: bytes en binario/hex y palabras de codigo
✔ vista del texto actual coincide con el .hfa real en los primeros bits
✔ paso 0: cola inicial ordenada, sin union
✔ paso 1: salen c y d, nace un nodo de 2
✔ ultimo paso: una sola raiz de 11 y el bosque la contiene completa
✔ fuera de rango y un solo simbolo
✔ describirCamino de b
✔ serieGrafica: orden por frecuencia, alturas en [0,1] y bits
✔ frecuencias de abracadabra
✔ codigos calculados a mano (c+d, b+r, cd+br, a+resto)
✔ ningun codigo es prefijo de otro (256 simbolos)
✔ casos borde del arbol: vacio y un solo simbolo
✔ la cola registrada coincide con el orden real de salida
✔ camino de un simbolo: ids y bits coherentes
✔ bits: empaquetar con relleno e ida y vuelta
✔ codificar (eficiente) produce lo mismo que empaquetar(texto de bits)
✔ formato: el ejemplo documentado de abracadabra (94 bytes) sale byte a byte igual
✔ formato: campos del encabezado
✔ formato: no guarda el texto original
✔ formato: rechaza archivos invalidos, truncados o alterados
✔ integridad ida y vuelta: texto normal
✔ integridad ida y vuelta: vacio
✔ integridad ida y vuelta: un solo simbolo
✔ integridad ida y vuelta: un solo byte
✔ integridad ida y vuelta: acentos y saltos de Windows
✔ integridad ida y vuelta: latin-1
✔ integridad ida y vuelta: los 256 bytes
✔ integridad: 200 entradas aleatorias reproducibles
✔ integridad: detecta un bit cambiado en los datos
✔ metricas y tamano legible
✔ simbolos y tabla
✔ layout: cada hoja una columna y padres centrados
✔ escribirHfa/leerHfa: tabla de 256 simbolos
✔ flujo: original -> .hfa -> recuperado, sin el original
✔ el analisis predice exactamente el tamano del .hfa real
✔ cada .hfa generado aqui tiene datos de largo ceil(bits/8)
✔ compatibilidad: Python comprime, JS descomprime (y al reves, byte a byte)
```

## 2. Integridad y métricas por archivo
| Archivo | Original (B) | .hfa (B) | Reducción % | Razón | Símbolos | Comprimir (ms) | Descomprimir (ms) | Idéntico |
|---|---|---|---|---|---|---|---|---|
| GPL-3.txt | 35,149 | 20,699 | 41.11 | 1.7 | 76 | 1.5 | 1.3 | ✅ |
| Apache-2.txt | 11,358 | 6,770 | 40.39 | 1.68 | 76 | 0.5 | 0.4 | ✅ |
| GFDL-1.txt | 22,955 | 13,576 | 40.86 | 1.69 | 76 | 0.9 | 0.7 | ✅ |

### SHA-256 original vs recuperado
- **GPL-3.txt**
  - original:   `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`
  - recuperado: `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` ✅ idéntico
- **Apache-2.txt**
  - original:   `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`
  - recuperado: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` ✅ idéntico
- **GFDL-1.txt**
  - original:   `110535522396708cea37c72a802c5e7e81391139f5f7985631c93ef242b206a4`
  - recuperado: `110535522396708cea37c72a802c5e7e81391139f5f7985631c93ef242b206a4` ✅ idéntico

## 3. Medición de complejidad
**Construcción del árbol** (n = símbolos distintos, tiempo medio por árbol): crece como n·log₂n, no como n².

| n | n·log₂n | µs por árbol |
|---|---|---|
| 2 | 2 | 2.1 |
| 4 | 8 | 2.2 |
| 8 | 24 | 1 |
| 16 | 64 | 1.6 |
| 32 | 160 | 3.7 |
| 64 | 384 | 8 |
| 128 | 896 | 18.2 |
| 256 | 2048 | 38.1 |

**Pipeline completo** (texto repetido L veces, mismos n símbolos): crece de forma lineal con L (ns por byte casi constante).

| L (bytes) | Tiempo (ms) | ns / byte |
|---|---|---|
| 35,149 | 1.1 | 31.4 |
| 70,298 | 2.2 | 30.7 |
| 140,596 | 4.2 | 29.6 |
| 281,192 | 8.3 | 29.5 |
| 562,384 | 16.8 | 29.8 |

> Los archivos de prueba son textos de licencias del sistema. La prueba con un libro de Project Gutenberg (T-01) y con un archivo nuevo (T-02) se corre con `npm run evidencias -- ruta/libro.txt` y se agrega aquí.
