// Genera evidencias/RESULTADOS.md y evidencias/resultados.json:
//   1) salida de las pruebas, 2) integridad SHA-256 y metricas por archivo, 3) medicion de complejidad.
// Uso:  npm run evidencias -- [archivo.txt ...]      (sin argumentos usa textos de ejemplo del sistema)
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename } from "node:path";
import { fileURLToPath } from "node:url";
import { aHex, comprimir, construirArbol, contarFrecuencias, descomprimir, generarCodigos, sha256, tamanoLegible } from "../src/core/index.js";

const web = fileURLToPath(new URL("..", import.meta.url));
const salida = fileURLToPath(new URL("../../evidencias/", import.meta.url));
mkdirSync(salida, { recursive: true });

const archivos = process.argv.slice(2);
if (!archivos.length) archivos.push(...["/usr/share/common-licenses/GPL-3", "/usr/share/common-licenses/Apache-2.0", "/usr/share/common-licenses/GFDL-1.3"].filter(existsSync));
const mejorDe = async (fn, n = 5) => { let m = Infinity; for (let i = 0; i < n; i++) { const t = performance.now(); await fn(); m = Math.min(m, performance.now() - t); } return m; };

// 1) pruebas
const t = spawnSync(process.execPath, ["--test", "--test-reporter=spec"], { cwd: web, encoding: "utf8" });
const resumenPruebas = (t.stdout + t.stderr).split("\n").filter((l) => /^ℹ (tests|pass|fail|skipped)/.test(l)).map((l) => l.replace("ℹ ", ""));
const lineasPruebas = (t.stdout + t.stderr).split("\n").filter((l) => /^\s*[✔✖]/.test(l)).map((l) => l.replace(/\s*\([\d.]+ms\)\s*$/, "")).join("\n");

// 2) archivos reales
const filas = [];
for (const ruta of archivos) {
  const datos = new Uint8Array(readFileSync(ruta));
  const nombre = basename(ruta).replace(/\.[^.]*$/, "") + ".txt";
  const hfa = await comprimir(datos, nombre);
  const rec = await descomprimir(new Uint8Array(hfa));
  const msC = await mejorDe(() => comprimir(datos, nombre));
  const msD = await mejorDe(() => descomprimir(hfa));
  const h1 = aHex(await sha256(datos));
  const h2 = aHex(await sha256(rec.datos));
  filas.push({ archivo: nombre, original: datos.length, hfa: hfa.length, reduccion: +(((datos.length - hfa.length) / datos.length) * 100).toFixed(2), razon: +(datos.length / hfa.length).toFixed(2), simbolos: contarFrecuencias(datos).size, msComprimir: +msC.toFixed(1), msDescomprimir: +msD.toFixed(1), sha256Original: h1, sha256Recuperado: h2, identico: h1 === h2 && rec.integridadOk });
}

// 3) complejidad: (a) arbol vs numero de simbolos distintos n, (b) pipeline vs largo L con n fijo
const arbolPorN = [];
for (const n of [2, 4, 8, 16, 32, 64, 128, 256]) {
  const f = new Map(Array.from({ length: n }, (_, i) => [i, 1 + ((i * 7919) % 1000)]));
  const reps = 4000;
  const t0 = performance.now();
  for (let i = 0; i < reps; i++) construirArbol(f);
  arbolPorN.push({ n, usPorArbol: +(((performance.now() - t0) / reps) * 1000).toFixed(1), nlogn: +(n * Math.log2(n)).toFixed(0) });
}
const base = readFileSync(archivos[0] ?? "/dev/null");
const porL = [];
for (const factor of [1, 2, 4, 8, 16]) {
  const datos = new Uint8Array(base.length * factor);
  for (let i = 0; i < factor; i++) datos.set(base, i * base.length);
  const ms = await mejorDe(() => comprimir(datos, "c.txt"), 3);
  porL.push({ L: datos.length, ms: +ms.toFixed(1), nsPorByte: +((ms * 1e6) / datos.length).toFixed(1) });
}

const tabla = (cols, rows) => [`| ${cols.map(([, t]) => t).join(" | ")} |`, `|${cols.map(() => "---").join("|")}|`, ...rows.map((r) => `| ${cols.map(([k]) => r[k]).join(" | ")} |`)].join("\n");
const md = `# Resultados y evidencias (generado automáticamente)

Generado con \`npm run evidencias\` el ${new Date().toISOString().slice(0, 10)} con Node ${process.version}. No editar a mano: se vuelve a generar.

## 1. Pruebas automáticas
${resumenPruebas.map((l) => `- ${l}`).join("\n")}

\`\`\`
${lineasPruebas}
\`\`\`

## 2. Integridad y métricas por archivo
${tabla([["archivo", "Archivo"], ["original", "Original (B)"], ["hfa", ".hfa (B)"], ["reduccion", "Reducción %"], ["razon", "Razón"], ["simbolos", "Símbolos"], ["msComprimir", "Comprimir (ms)"], ["msDescomprimir", "Descomprimir (ms)"], ["identico", "Idéntico"]], filas.map((f) => ({ ...f, original: f.original.toLocaleString("en-US"), hfa: f.hfa.toLocaleString("en-US"), identico: f.identico ? "✅" : "❌" })))}

### SHA-256 original vs recuperado
${filas.map((f) => `- **${f.archivo}**\n  - original:   \`${f.sha256Original}\`\n  - recuperado: \`${f.sha256Recuperado}\` ${f.identico ? "✅ idéntico" : "❌ DIFERENTE"}`).join("\n")}

## 3. Medición de complejidad
**Construcción del árbol** (n = símbolos distintos, tiempo medio por árbol): crece como n·log₂n, no como n².

${tabla([["n", "n"], ["nlogn", "n·log₂n"], ["usPorArbol", "µs por árbol"]], arbolPorN)}

**Pipeline completo** (texto repetido L veces, mismos n símbolos): crece de forma lineal con L (ns por byte casi constante).

${tabla([["L", "L (bytes)"], ["ms", "Tiempo (ms)"], ["nsPorByte", "ns / byte"]], porL.map((r) => ({ ...r, L: r.L.toLocaleString("en-US") })))}

> Los archivos de prueba son textos de licencias del sistema. La prueba con un libro de Project Gutenberg (T-01) y con un archivo nuevo (T-02) se corre con \`npm run evidencias -- ruta/libro.txt\` y se agrega aquí.
`;
writeFileSync(salida + "RESULTADOS.md", md);
writeFileSync(salida + "resultados.json", JSON.stringify({ pruebas: resumenPruebas, archivos: filas, arbolPorN, porL }, null, 2));
console.log(md.split("\n").slice(0, 12).join("\n"));
if (t.status !== 0 || filas.some((f) => !f.identico)) { console.error("HAY FALLOS: revisa evidencias/RESULTADOS.md"); process.exit(1); }
