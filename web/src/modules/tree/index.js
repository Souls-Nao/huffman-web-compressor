// STUB del paquete 0: el dueno del modulo reemplaza este archivo completo.
import { h, reemplazar } from "../../app/dom.js";

export function montar(el) {
  reemplazar(el, h("div", { clase: "vacio" }, "Modulo pendiente: tree"));
}

// Contrato que usa el inspector: debe conservarse al implementar el modulo.
export function montarArbol() {
  return { actualizar() {}, destruir() {} };
}
