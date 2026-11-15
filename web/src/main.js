// Punto de entrada: crea el store, calcula el analisis cuando cambia la entrada y monta los modulos.
// Cada modulo exporta montar(el, store). Un error en un modulo no tumba a los demas.
import { montarFlujo } from "./app/flujo.js";
import { crearStore } from "./app/store.js";
import { h, reemplazar, alerta } from "./app/dom.js";
import { analizar } from "./core/index.js";
import * as input from "./modules/input/index.js";
import * as steps from "./modules/steps/index.js";
import * as tree from "./modules/tree/index.js";
import * as compress from "./modules/compress/index.js";
import * as inspector from "./modules/inspector/index.js";

// progreso = { inspeccionado, descomprimido, verificado }: lo marca el inspector para la barra de flujo.
// inspeccionar = marca de tiempo: compress la cambia para que el inspector cargue el .hfa recien creado.
const store = crearStore({ entrada: null, analisis: null, comprimido: null, simbolo: null, progreso: {}, inspeccionar: 0 });

// Entrada nueva -> analisis nuevo (frecuencias, arbol, codigos, pasos). Se descarta lo anterior.
store.alCambiar(["entrada"], ({ entrada }) => {
  const analisis = entrada ? analizar(entrada.datos, entrada.nombre) : null;
  store.actualizar({ analisis, comprimido: null, simbolo: null });
});

const modulos = [
  ["mod-input", input],
  ["mod-steps", steps],
  ["mod-tree", tree],
  ["mod-compress", compress],
  ["mod-inspector", inspector],
];

for (const [id, modulo] of modulos) {
  const el = document.getElementById(id);
  try {
    modulo.montar(el, store);
  } catch (error) {
    console.error(id, error);
    reemplazar(el, alerta("error", `No se pudo cargar este módulo: ${error.message}`));
  }
}
montarFlujo(document.getElementById("flujo"), store);
window.__huffman = { store }; // solo para depurar en la consola
