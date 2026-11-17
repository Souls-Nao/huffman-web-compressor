// Zoom y arrastre para un <svg> mediante su viewBox. Sin dependencias.
export function crearViewport(svg, ancho, alto) {
  let caja = { x: 0, y: 0, w: ancho, h: alto };
  const aplicar = () => svg.setAttribute("viewBox", `${caja.x} ${caja.y} ${caja.w} ${caja.h}`);
  const zoom = (factor, cx = caja.x + caja.w / 2, cy = caja.y + caja.h / 2) => {
    const w = Math.min(ancho * 1.2, Math.max(60, caja.w * factor));
    const k = w / caja.w;
    caja = { x: cx - (cx - caja.x) * k, y: cy - (cy - caja.y) * k, w, h: caja.h * k };
    aplicar();
  };
  const aPunto = (e) => {
    const r = svg.getBoundingClientRect();
    return { x: caja.x + ((e.clientX - r.left) / r.width) * caja.w, y: caja.y + ((e.clientY - r.top) / r.height) * caja.h };
  };
  let arrastre = null;
  svg.addEventListener("wheel", (e) => { e.preventDefault(); const p = aPunto(e); zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, p.x, p.y); }, { passive: false });
  svg.addEventListener("pointerdown", (e) => { if (e.target.closest("[data-simbolo]")) return; arrastre = { cx: e.clientX, cy: e.clientY, caja: { ...caja } }; svg.setPointerCapture(e.pointerId); svg.classList.add("arbol--arrastrando"); });
  svg.addEventListener("pointermove", (e) => {
    if (!arrastre) return;
    const r = svg.getBoundingClientRect();
    caja = { ...arrastre.caja, x: arrastre.caja.x - ((e.clientX - arrastre.cx) / r.width) * caja.w, y: arrastre.caja.y - ((e.clientY - arrastre.cy) / r.height) * caja.h };
    aplicar();
  });
  const soltar = () => { arrastre = null; svg.classList.remove("arbol--arrastrando"); };
  svg.addEventListener("pointerup", soltar);
  svg.addEventListener("pointercancel", soltar);
  return {
    acercar: () => zoom(1 / 1.3),
    alejar: () => zoom(1.3),
    ajustar: () => { caja = { x: 0, y: 0, w: ancho, h: alto }; aplicar(); },
    // Ajusta la vista a un rectangulo del dibujo (el camino resaltado), con margen y sin deformar.
    enfocarCaja(x0, y0, x1, y1) {  // 'this' = el objeto devuelto
      const r = svg.getBoundingClientRect();
      const aspecto = r.width > 0 && r.height > 0 ? r.height / r.width : alto / ancho;
      const margen = 70;
      let w = Math.max(x1 - x0 + margen * 2, 280);
      if (w * aspecto < y1 - y0 + margen * 2) w = (y1 - y0 + margen * 2) / aspecto;
      if (w >= ancho) return this.ajustar(); // el camino ya abarca el arbol: se muestra completo
      const hh = w * aspecto;
      caja = { x: (x0 + x1) / 2 - w / 2, y: (y0 + y1) / 2 - hh / 2, w, h: hh };
      aplicar();
    },
    aplicar,
  };
}
