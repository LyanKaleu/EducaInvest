// Movimento com JavaScript: só melhoria progressiva sobre o movimento.css.
// Sem este arquivo (JS desligado, rede caiu, navegador antigo) toda tela
// funciona igual; ele só acrescenta o que CSS sozinho não faz.
// Padrões do transitions.dev, com os tempos lidos dos tokens do tokens.css.

const raiz = document.documentElement;

// O CSS que depende do JS fica sob .js, para nunca esconder nada sem ele.
raiz.classList.add("js");

/** Quem pediu menos movimento no sistema recebe só a versão suave. */
export const poucoMovimento = matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;

// ---------------------------------------------------------------------------
// Gasto/Entrada: pílula que desliza até a opção marcada (tabs sliding)
// ---------------------------------------------------------------------------

/** Põe a pílula no grupo e a move a cada troca de opção. */
function pilulaDoSegmento(grupo) {
  const opcoes = [...grupo.querySelectorAll(".segmento-opcao")];
  const pilula = document.createElement("span");
  pilula.className = "pilula";
  pilula.setAttribute("aria-hidden", "true");
  grupo.append(pilula); // depois da <legend>, que precisa ser a primeira

  function mover(animar) {
    const alvo = opcoes.find((opcao) => opcao.querySelector("input").checked);
    if (!alvo) {
      delete grupo.dataset.marcada;
      return;
    }
    // Na primeira posição e no redimensionamento a pílula vai direto, sem
    // deslizar desde o canto (erro comum apontado pelo transitions.dev).
    if (!animar) pilula.style.transition = "none";
    pilula.style.width = `${alvo.offsetWidth}px`;
    pilula.style.height = `${alvo.offsetHeight}px`;
    pilula.style.transform =
      `translate(${alvo.offsetLeft}px, ${alvo.offsetTop}px)`;
    grupo.dataset.marcada = alvo.classList.contains("gasto")
      ? "gasto"
      : "entrada";
    if (!animar) {
      void pilula.offsetWidth; // aplica a posição antes de devolver a transição
      pilula.style.transition = "";
    }
  }

  grupo.addEventListener("change", () => mover(true));
  addEventListener("resize", () => mover(false));
  mover(false);
}

document.querySelectorAll(".segmento").forEach(pilulaDoSegmento);

// ---------------------------------------------------------------------------
// Painel: XP que rola e barra do nível que enche desde onde estava
// ---------------------------------------------------------------------------

// O localStorage pode faltar ou recusar (aba anônima, dados bloqueados): aí o
// painel só não anima, nunca quebra.
function lerVisto(chave) {
  try {
    return JSON.parse(localStorage.getItem(chave));
  } catch {
    return null;
  }
}

function guardarVisto(chave, valor) {
  try {
    localStorage.setItem(chave, JSON.stringify(valor));
  } catch {
    // sem armazenamento, sem animação na próxima visita
  }
}

/** Anima a barra de `de` a `para` (0 a 100), com ease-out. */
function encherBarra(barra, de, para, duracao) {
  barra.classList.add("enchendo"); // desliga a revelação do CSS
  const inicio = performance.now();
  const passo = (agora) => {
    const t = Math.min(1, (agora - inicio) / duracao);
    const suave = 1 - (1 - t) ** 3;
    barra.value = de + (para - de) * suave;
    if (t < 1) requestAnimationFrame(passo);
  };
  barra.value = de;
  requestAnimationFrame(passo);
}

/** Compara com o último XP visto neste aparelho e celebra o que subiu. */
async function animarNivel(cartao) {
  const chave = `educainvest:nivel:${cartao.dataset.aluno}`;
  const agora = {
    xp: Number(cartao.dataset.xp),
    nivel: Number(cartao.dataset.nivel),
    percentual: Number(cartao.dataset.percentual),
  };
  const antes = lerVisto(chave);
  guardarVisto(chave, agora);
  // Primeira visita, nada novo ou menos movimento: a tela fica como veio.
  if (!antes || antes.xp >= agora.xp || poucoMovimento) return;

  const { rolar } = await import("./contador.js");
  const numero = cartao.querySelector("#xp-total");
  // O leitor de tela lê só o valor final; o tambor é decorativo.
  const leitor = document.createElement("span");
  leitor.className = "oculto";
  leitor.textContent = `${agora.xp} XP`;
  const tambor = document.createElement("span");
  tambor.className = "t-reel";
  tambor.setAttribute("aria-hidden", "true");
  const sufixo = document.createElement("span");
  sufixo.setAttribute("aria-hidden", "true");
  sufixo.textContent = " XP";
  numero.replaceChildren(leitor, tambor, sufixo);
  rolar(tambor, antes.xp, agora.xp);

  const barra = cartao.querySelector("progress");
  const subiu = agora.nivel > antes.nivel;
  encherBarra(barra, subiu ? 0 : antes.percentual, agora.percentual, 900);
  if (subiu) cartao.classList.add("subiu");
}

const cartaoNivel = document.querySelector(".indicador.nivel[data-xp]");
if (cartaoNivel) animarNivel(cartaoNivel);
