// Helpers para crear DOM/SVG sin innerHTML (todo el texto entra como textContent: sin XSS).
const NS = { html: "http://www.w3.org/1999/xhtml", svg: "http://www.w3.org/2000/svg" };

function crear(ns, etiqueta, props = {}, hijos = []) {
  const el = document.createElementNS(NS[ns], etiqueta);
  for (const [clave, valor] of Object.entries(props ?? {})) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (clave.startsWith("on") && typeof valor === "function") el.addEventListener(clave.slice(2).toLowerCase(), valor);
    else if (clave === "clase") el.setAttribute("class", valor);
    else if (clave === "dataset") Object.assign(el.dataset, valor);
    else if (clave === "estilo") {
      // Las variables CSS (--algo) solo se aplican con setProperty.
      for (const [k, v] of Object.entries(valor)) k.startsWith("--") ? el.style.setProperty(k, v) : (el.style[k] = v);
    }
    else el.setAttribute(clave, valor === true ? "" : String(valor));
  }
  agregar(el, hijos);
  return el;
}

function agregar(el, hijos) {
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
}

export const h = (etiqueta, props, ...hijos) => crear("html", etiqueta, props, hijos);
export const s = (etiqueta, props, ...hijos) => crear("svg", etiqueta, props, hijos);

export function reemplazar(el, ...hijos) {
  el.replaceChildren();
  agregar(el, hijos);
  return el;
}

export function descargar(bytes, nombre, tipo = "application/octet-stream") {
  const url = URL.createObjectURL(new Blob([bytes], { type: tipo }));
  const enlace = h("a", { href: url, download: nombre });
  document.body.append(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// Tarjetas de metricas (usadas por compress e inspector).
export function tarjetaMetrica(etiqueta, valor, nota) {
  return h("div", { clase: "metrica" }, h("span", { clase: "metrica__etiqueta" }, etiqueta), h("strong", { clase: "metrica__valor" }, valor), nota && h("span", { clase: "metrica__nota" }, nota));
}

export function alerta(tipo, ...contenido) {
  return h("div", { clase: `alerta alerta--${tipo}`, role: tipo === "error" ? "alert" : "status" }, ...contenido);
}
