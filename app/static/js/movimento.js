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
