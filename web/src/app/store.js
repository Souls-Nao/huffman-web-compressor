// Estado compartido minimo (publicar/suscribir). Los modulos NO se llaman entre si:
// leen y escriben aqui. Es la misma idea que un contexto de React, por eso migra facil.
//
// Claves: entrada {nombre, datos, origen} | analisis (core/analisis.js) | comprimido {nombre, bytes, metricas, ms}
//         | simbolo (byte seleccionado o null)
export function crearStore(inicial = {}) {
  let estado = { ...inicial };
  const oyentes = new Set();
  return {
    obtener: () => estado,
    actualizar(parcial) {
      const anterior = estado;
      estado = { ...estado, ...parcial };
      for (const oyente of [...oyentes]) oyente(estado, anterior);
    },
    suscribir(oyente) {
      oyentes.add(oyente);
      return () => oyentes.delete(oyente);
    },
    // Llama a `fn(estado)` ahora y cada vez que cambie alguna de las claves indicadas.
    alCambiar(claves, fn) {
      fn(estado);
      return this.suscribir((nuevo, anterior) => {
        if (claves.some((clave) => nuevo[clave] !== anterior[clave])) fn(nuevo);
      });
    },
  };
}
