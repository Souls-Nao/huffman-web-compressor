# Arquitectura de la versión web (JS + CSS)

La app Streamlit original se conserva como **referencia** (`app.py`, `huffman/`). La interfaz nueva vive en `web/` y está pensada para migrar a **React Native (Web)** sin reescribir la lógica.

## 1. Capas

```
web/src/
├── core/            LÓGICA PURA (sin DOM, sin red). Port de huffman/*.py. Se reutiliza tal cual en React Native.
├── app/             store (publicar/suscribir), helpers DOM, barra de flujo.
├── modules/<x>/     un módulo = una sección de la página.
│     viewmodel.js     datos listos para mostrar (puro, probado con node:test). Se reutiliza tal cual.
│     index.js         vista DOM:  montar(el, store).  Es lo ÚNICO que se reescribe en React Native.
│     <x>.css          estilos del módulo (usan solo variables de styles/tokens.css).
└── styles/          tokens (colores, radios, tipografía; modo oscuro), base y layout.
```

Regla de dependencias: `modules → core`, `modules → app`; **ningún módulo importa a otro**, salvo el inspector que usa el componente público `montarArbol` de `tree` (contrato abajo). La comunicación va por el `store`.

## 2. Estado compartido (`store`)

| Clave | Quién la escribe | Contenido |
|---|---|---|
| `entrada` | input | `{ nombre, datos: Uint8Array, origen, libro? }` |
| `analisis` | main.js (al cambiar `entrada`) | frecuencias, árbol, códigos, pasos, bits totales, tamaño final exacto |
| `comprimido` | compress | `{ nombre, bytes, ms, metricas }` |
| `simbolo` | tree / inspector | byte seleccionado (resalta su camino en todos los árboles) |
| `progreso` | inspector | `{ inspeccionado, descomprimido, verificado }` (barra de flujo) |
| `inspeccionar` | compress | marca de tiempo: pide al inspector cargar el `.hfa` recién creado |

## 3. Contratos entre módulos

```js
// cada módulo
export function montar(el, store) {}

// tree/index.js (lo usa el inspector)
export function montarArbol(el, { raiz, codigos, simbolo, onSeleccionar }) → { actualizar({ raiz, codigos, simbolo }), destruir() }
```

## 4. Propiedad de archivos (cero conflictos)

| Carpeta / archivo | Dueño |
|---|---|
| `web/package.json`, `web/index.html`, `web/src/{core,app,styles}`, `web/src/main.js` | Paquete 0 (base) |
| `web/src/modules/input`, `web/src/modules/compress`, `web/proxy` | Dev1 |
| `web/src/modules/tree` | Dev2 |
| `web/src/modules/steps`, `web/src/modules/inspector` | Dev3 |
| `web/tests`, `web/scripts`, `evidencias`, `docs`, `README.md`, `.github` | Dev4 |

## 5. Gutenberg y CORS
`gutenberg.org` no envía cabeceras CORS, así que el navegador no puede leerlo directo (ver `PLAN.md` §1.1). `web/proxy/worker.js` es un proxy gratuito (Cloudflare Workers) que solo reenvía dos rutas fijas (búsqueda OPDS y texto plano de un libro) y agrega CORS. En local, `npm start` usa el mismo código como `/gutenberg/*` (mismo origen).

## 6. Migración a React Native (Web)

| Pieza | ¿Cambia? | Cómo |
|---|---|---|
| `core/*`, `*/viewmodel.js`, `store.js` | No | JS puro. El store se envuelve en un contexto o hook (`useSyncExternalStore(store.suscribir, store.obtener)`). |
| Vistas `modules/*/index.js` | Sí | Cada `montar(el, store)` pasa a un componente: `h("div")`→`<View>`, `h("p")`→`<Text>`, `h("button")`→`<Pressable>`, `h("table")`→`FlatList`. |
| Árbol SVG (`tree/render.js`) | Poco | `s("svg"/"g"/"line"/"circle"/"text")` → `react-native-svg` (`Svg`, `G`, `Line`, `Circle`, `Text`). La geometría ya sale de `core/layout.js`. |
| Zoom/arrastre (`viewport.js`) | Sí | Reemplazar por `PanResponder` o `react-native-gesture-handler`; la lógica de la caja (`viewBox`) se conserva. |
| CSS | Sí | `tokens.css` → objeto `tokens` de JS; clases → `StyleSheet.create`. Los nombres de las variables se mantienen. |
| Archivos (subir/descargar) | Sí | `<input type=file>` → `expo-document-picker`; `Blob`+`<a download>` → `expo-sharing`/`expo-file-system`. Web: igual que hoy. |
| SHA-256 | No en web | `crypto.subtle` existe en navegador y Node; en nativo usar `expo-crypto`. |

Orden recomendado: 1) contexto del store, 2) `compress` e `input` (formularios simples), 3) `inspector`, 4) `steps`, 5) `tree` (el más costoso por gestos).
