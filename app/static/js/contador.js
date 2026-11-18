// Contador que rola os dígitos num tambor 3D até o valor novo e assenta com
// uma mola (transitions.dev: spinning counter). Só o painel do aluno carrega
// este arquivo, sob demanda (import() no movimento.js), quando o XP subiu.
// Os tempos e medidas vêm das variables --reel-* do .t-reel (movimento.css).

const STEP = (50 * Math.PI) / 180; // ângulo do tambor entre dois dígitos
const ENTER_MS = 120; // do repouso até rolar
const FADE_END = 1.8; // a quantos passos do meio o dígito some
const LAND_AT = 0.6; // a quantos passos do meio o alvo começa a pousar
const ARRIVE_AT = 0.29; // parte da mola em que ele chega ao meio
const CLEAR_MS = 200; // desfoque e vizinhos somem no começo da mola

function token(el, name, fallback) {
  const v = parseFloat(getComputedStyle(el).getPropertyValue(name));
  return Number.isNaN(v) ? fallback : v;
}

// As medidas estão em em (o desfoque é uma curva no tamanho da fonte), então
// são medidas em px no próprio tambor e seguem o tamanho do número.
function length(el, name, fallbackEm) {
  const probe = document.createElement("span");
  probe.style.position = "absolute";
  probe.style.visibility = "hidden";
  probe.style.width = `var(${name})`;
  el.appendChild(probe);
  const px = probe.getBoundingClientRect().width;
  probe.remove();
  return px || fallbackEm * (parseFloat(getComputedStyle(el).fontSize) || 24);
}

function bezier([x1, y1, x2, y2]) {
  const at = (a, b, t) =>
    3 * a * t * (1 - t) * (1 - t) + 3 * b * t * t * (1 - t) + t * t * t;
  return (x) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let lo = 0;
    let hi = 1;
    let t = x;
    for (let i = 0; i < 20; i++) {
      if (at(x1, x2, t) < x) lo = t;
      else hi = t;
      t = (lo + hi) / 2;
    }
    return at(y1, y2, t);
  };
}

function readTokens(el) {
  const m = getComputedStyle(el)
    .getPropertyValue("--reel-ease")
    .match(/cubic-bezier\(([^)]+)\)/);
  return {
    stepDur: token(el, "--reel-step-dur", 130),
    stagger: token(el, "--reel-stagger", 90),
    ease: bezier(m ? m[1].split(",").map(parseFloat) : [0.35, -0.02, 0.43, 1]),
    offset: length(el, "--reel-side-offset", 0.52),
    sideScale: token(el, "--reel-side-scale", 0.7),
    sideBlur: length(el, "--reel-side-blur", 0.083),
    sideOpacity: token(el, "--reel-side-opacity", 0.17),
    centerScale: token(el, "--reel-center-scale", 0.9),
    centerBlur: length(el, "--reel-center-blur", 0.042),
    anticDur: token(el, "--reel-antic-dur", 100),
    anticScale: token(el, "--reel-antic-scale", 0.94),
    anticLift: length(el, "--reel-antic-lift", 0.125),
    landDur: token(el, "--reel-land-dur", 740),
    landPeak: token(el, "--reel-land-peak", 1.03),
  };
}

function smooth(x) {
  const y = Math.max(0, Math.min(1, x));
  return y * y * (3 - 2 * y);
}

// Onda amortecida: começa em 1, cruza o 0, passa do ponto (a mola) e para.
function wave(s) {
  return s >= 1 ? 0 : Math.exp(-3 * s) * Math.cos(3 * Math.PI * s) * (1 - s);
}
const WAVE_TROUGH = (() => {
  let low = 0;
  for (let i = 1; i < 400; i++) low = Math.min(low, wave(i / 400));
  return -low;
})();

function buildColumns(el, str) {
  el.replaceChildren();
  const cols = [];
  for (const ch of str) {
    if (ch < "0" || ch > "9") {
      const sep = document.createElement("span");
      sep.className = "t-reel-sep";
      sep.textContent = ch;
      el.appendChild(sep);
      continue;
    }
    const col = document.createElement("span");
    col.className = "t-reel-col";
    const sizer = document.createElement("span");
    sizer.className = "t-reel-sizer";
    sizer.textContent = "0";
    col.appendChild(sizer);
    const cells = [];
    for (let d = 0; d < 10; d++) {
      const cell = document.createElement("span");
      cell.className = "t-reel-digit";
      cell.textContent = String(d);
      col.appendChild(cell);
      cells.push(cell);
    }
    el.appendChild(col);
    cols.push({ cells, digit: Number(ch) });
  }
  return cols;
}

function rest(col, digit) {
  col.cells.forEach((cell, d) => {
    cell.style.transform = "none";
    cell.style.filter = "none";
    cell.style.zIndex = "";
    cell.style.opacity = d === digit ? "1" : "0";
  });
}

function look(dist, middle, o) {
  const angle = Math.min(dist * STEP, Math.PI / 2);
  // 1 no meio, 0 a um passo, abaixo de 0 mais para trás.
  const face = (Math.cos(angle) - Math.cos(STEP)) / (1 - Math.cos(STEP));
  return {
    angle,
    scale: o.sideScale + (middle - o.sideScale) * face,
    back:
      dist <= 1
        ? 1 + (o.sideOpacity - 1) * dist
        : o.sideOpacity * (1 - (dist - 1) / (FADE_END - 1)),
  };
}

function place(col, pos, spread, middle, o, land) {
  const radius = o.offset / Math.sin(STEP);
  col.cells.forEach((cell, d) => {
    let p = (((d - pos) % 10) + 10) % 10;
    if (p > 5) p -= 10;
    const dist = Math.abs(p);
    if (dist >= FADE_END) {
      cell.style.opacity = "0";
      return;
    }
    const l = look(dist, middle, o);
    // Os próximos dígitos ficam acima do meio, então o tambor gira para baixo.
    let y = (p < 0 ? 1 : -1) * radius * Math.sin(l.angle);
    const blur =
      (o.centerBlur + (o.sideBlur - o.centerBlur) * Math.min(dist, 1)) *
      spread;
    const away = Math.max(0, Math.min(1, (dist - 0.3) / 0.5));
    let opacity = l.back * (1 - (1 - spread) * away);
    let scale = l.scale;
    let z = 100 - Math.round(dist * 10);
    if (land && d === col.digit) {
      y = y * land.arrive + land.lift;
      scale = land.scale;
      opacity = land.opacity;
      z = 200;
    }
    cell.style.transform =
      `translateY(${y.toFixed(2)}px) scale(${scale.toFixed(4)})`;
    cell.style.filter = blur > 0.01 ? `blur(${blur.toFixed(2)}px)` : "none";
    cell.style.opacity = opacity.toFixed(3);
    cell.style.zIndex = String(z);
  });
}

/**
 * Rola `el` de um número a outro. Devolve uma função que cancela.
 * @param {HTMLElement} el o .t-reel (escondido do leitor de tela)
 * @param {number} from valor de partida
 * @param {number} to valor final
 */
export function rolar(el, from, to) {
  const cols = buildColumns(el, String(to));
  const o = readTokens(el);
  // Cada coluna parte do seu dígito no número antigo, alinhado à direita.
  const fromDigits = String(from)
    .padStart(cols.length, "0")
    .slice(-cols.length);
  cols.forEach((c, i) => {
    c.from = Number(fromDigits[i]);
    rest(c, c.from);
    if (c.from === c.digit) c.done = true;
  });
  const t0 = performance.now();
  let raf = 0;
  const tick = () => {
    const t = performance.now() - t0;
    let running = false;
    cols.forEach((c, i) => {
      if (c.done) return;
      const local = t - i * o.stagger;
      if (local <= 0) {
        running = true;
        return;
      }
      const total = (c.digit - c.from + 10) % 10;
      // Tempo fixo por número: rolar mais leva mais tempo.
      const pos = c.from + total * o.ease(local / (total * o.stepDur));
      const enter = Math.min(1, local / ENTER_MS);
      if (c.landAt === undefined && c.from + total - pos < LAND_AT) {
        c.landAt = t;
      }
      const since = c.landAt === undefined ? -1 : t - c.landAt;
      if (since >= o.anticDur + o.landDur) {
        rest(c, c.digit);
        c.done = true;
        return;
      }
      running = true;
      const middle = 1 + (o.centerScale - 1) * enter;
      let spread = enter;
      let land = null;
      if (since >= 0) {
        // Parte de como o alvo está agora, para nada pular.
        if (!c.landFrom) c.landFrom = look(c.from + total - pos, middle, o);
        const arrive =
          1 - smooth(since / (o.anticDur + o.landDur * ARRIVE_AT));
        if (since < o.anticDur) {
          // Antecipação: recua um pouco contra o giro.
          const a = smooth(since / o.anticDur);
          land = {
            scale: c.landFrom.scale + (o.anticScale - c.landFrom.scale) * a,
            lift: -o.anticLift * a,
            opacity: c.landFrom.back + (1 - c.landFrom.back) * a,
            arrive,
          };
        } else {
          // Mola: entra no meio, passa do ponto e assenta.
          const sp = since - o.anticDur;
          const sn = sp / o.landDur;
          const w = wave(sn);
          land = {
            scale:
              sn < 1 / 6
                ? 1 + (o.anticScale - 1) * w
                : 1 - ((o.landPeak - 1) * w) / WAVE_TROUGH,
            lift: -o.anticLift * w,
            opacity: 1,
            arrive,
          };
          spread = 1 - Math.min(1, sp / CLEAR_MS);
        }
      }
      place(c, pos, spread, middle, o, land);
    });
    if (running) raf = requestAnimationFrame(tick);
  };
  tick();
  return () => cancelAnimationFrame(raf);
}
