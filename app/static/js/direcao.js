// Direção da troca de página (transitions.dev: page side-by-side).
// Script clássico no <head>: o evento pagereveal acontece antes da primeira
// pintura, e um módulo (defer) chegaria tarde. Sem suporte à Navigation API
// ou às view transitions entre documentos, a troca fica no esmaecimento padrão.
//
// Ir para um item à direita no menu (ou entrar num detalhe) desliza para a
// esquerda ("avanca"); o caminho contrário, inclusive o botão Voltar, "volta".
{
  /** Posição do item do menu que contém o caminho e a profundidade. */
  const lugar = (url) => {
    const caminho = new URL(url).pathname;
    const itens = [
      ...document.querySelectorAll(".menu-aluno a, .menu-topo a"),
    ].map((a) => new URL(a.href).pathname);
    let indice = -1;
    let maior = 0;
    itens.forEach((item, i) => {
      if (caminho.startsWith(item) && item.length > maior) {
        indice = i;
        maior = item.length;
      }
    });
    const profundidade = caminho.split("/").filter(Boolean).length;
    return { indice, profundidade };
  };

  const direcao = (de, para) => {
    if (de.indice < 0 || para.indice < 0) return null;
    if (de.indice !== para.indice) {
      return para.indice > de.indice ? "avanca" : "volta";
    }
    if (para.profundidade === de.profundidade) return null;
    return para.profundidade > de.profundidade ? "avanca" : "volta";
  };

  addEventListener("pagereveal", (evento) => {
    const ativacao = window.navigation?.activation;
    if (!evento.viewTransition || !ativacao?.from || !ativacao.entry) return;
    // O menu já existe aqui: o <link rel="expect" blocking="render"> do
    // base.html segura a primeira pintura (e o pagereveal) até o <main>.
    const tipo = direcao(lugar(ativacao.from.url), lugar(ativacao.entry.url));
    if (tipo) evento.viewTransition.types.add(tipo);
  });
}
