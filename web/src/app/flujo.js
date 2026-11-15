// Barra de flujo: SUBIR/BUSCAR -> ANALIZAR -> CONSTRUIR HUFFMAN -> COMPRIMIR -> INSPECCIONAR -> DESCOMPRIMIR -> VERIFICAR
export function montarFlujo(el, store) {
  const pasos = [...el.querySelectorAll("[data-paso]")];
  const hecho = {
    entrada: (e) => !!e.entrada,
    analizar: (e) => !!e.analisis,
    huffman: (e) => !!e.analisis?.raiz,
    comprimir: (e) => !!e.comprimido,
    inspeccionar: (e) => !!e.progreso?.inspeccionado,
    descomprimir: (e) => !!e.progreso?.descomprimido,
    verificar: (e) => !!e.progreso?.verificado,
  };
  store.alCambiar(["entrada", "analisis", "comprimido", "progreso"], (estado) => {
    let siguiente = null;
    for (const paso of pasos) {
      const listo = hecho[paso.dataset.paso]?.(estado) ?? false;
      paso.classList.toggle("flujo__paso--hecho", listo);
      paso.classList.remove("flujo__paso--actual");
      if (!listo && !siguiente && hecho[paso.dataset.paso]) siguiente = paso;
    }
    siguiente?.classList.add("flujo__paso--actual");
  });
}
