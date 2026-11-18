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
