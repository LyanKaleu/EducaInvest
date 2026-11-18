# DESIGN.md · EducaInvest

Guia visual do EducaInvest para gerar telas em ferramentas de design (Claude Design, Google Stitch, Gemini).
Descreve o visual que existe hoje nos arquivos de `app/static/css/` (o do protótipo navegável, aplicado em 16/11/2026) e as restrições do código. A fonte da verdade continua sendo o CSS.
Se uma proposta nova for aprovada, atualize este arquivo junto com o CSS.

## 1. Produto e público
- **O que é:** app web de gestão financeira gamificada. O aluno registra entradas e gastos, guarda dinheiro em metas e ganha XP com missões. O professor acompanha a turma.
- **Quem usa:** jovens de 16 a 24 anos, quase sempre no **celular**, muitos no primeiro contato com controle de dinheiro. O professor usa mais no computador.
- **Tom:** amigável, direto e encorajador, sem infantilizar. Frases curtas em português do Brasil, falando com "você". Comemora conquistas ("Parabéns!") sem exagero. Nunca culpa o aluno por gastar.
- **Sensação desejada:** um app de banco simples misturado com o progresso de um jogo. Confiável no dinheiro, leve na gamificação.

## 2. Restrições técnicas (obrigatórias)
O design precisa caber nestas regras. Proposta que depende de algo fora delas não é implementável.
- **HTML renderizado no servidor (Jinja), com JavaScript só como melhoria progressiva.** Toda ação é um link ou um formulário que recarrega a página, e toda tela funciona igual com o JS desligado. O JS (`app/static/js/`, sem framework e sem build) só acrescenta movimento: a pílula do Gasto/Entrada, o XP rolando e a direção da troca de página. Nada de modal, drawer, carrossel, tooltip, drag and drop ou gráfico interativo.
- **CSS puro, um arquivo por assunto** em `app/static/css/` (`tokens`, `base`, `navegacao`, `aluno`, `professor`, `entrada`, `movimento`), carregados em ordem pelo `base.html`, sem `@import` e sem etapa de build. Sem framework (sem Tailwind, sem Bootstrap) e sem fonte externa. Animação só em CSS, toda em `movimento.css`, conforme a seção 7a. Sem `style` inline: a política de segurança (CSP) bloqueia.
- **Gráficos:** só o que dá para fazer com HTML e CSS: `<progress>`, barras com largura em %, números grandes. Sem bibliotecas de gráfico.
- **Ícones:** SVG inline de traço, sempre acompanhados de texto. Nada de emoji. Nenhuma informação só no ícone.
- **Mobile-first:** tudo funciona em 375px de largura. O conteúdo fica numa coluna de no máximo 40rem (640px) centralizada, também no desktop.
- **Acessibilidade (WCAG AA):** contraste de pelo menos 4,5:1 para texto, foco do teclado sempre visível, área de toque de pelo menos 44px, e cor nunca é a única pista (o sinal "-" vai no valor, o status vai escrito).
- **Dinheiro:** formato `R$ 1.234,56`, números com algarismos tabulares. Saldo negativo aparece como `-R$ 10,50`.

## 3. Cores
Paleta curta. Verde é a cor da marca e do dinheiro que entra; vermelho é gasto, erro e excluir; azul é foco e "em andamento".

O app tem tema claro e escuro e segue o tema do sistema (`prefers-color-scheme`), sem botão e sem JavaScript. Só as cores mudam; forma, espaço e movimento são os mesmos. Todas as cores ficam em `tokens.css`, e nenhum outro arquivo de CSS tem cor fixa (o teste `tests/unit/test_css_tokens.py` confere isso e calcula o contraste de cada par de texto e fundo nos dois temas).

**Verde e vermelho têm dois papéis.** O token base (`--primaria`, `--perigo`) é **fundo** com texto branco, faixa ou borda decorativa. O `-texto` (`--primaria-texto`, `--perigo-texto`) é **texto e contorno** sobre fundo neutro: links, valores, mensagens de erro, borda do campo com erro e da resposta do quiz. No claro os dois têm o mesmo valor; no escuro o `-texto` clareia para aparecer sobre o fundo escuro.

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--texto` | `#1a1a1a` | `#e6ece8` | texto principal |
| `--texto-suave` | `#555555` | `#a9b4ae` | rótulos, dicas e itens inativos do menu |
| `--fundo` | `#ffffff` | `#1b2320` | cartões e campos |
| `--suave` | `#f3f4f2` | `#111715` | fundo da página e trilho das barras |
| `--divisoria` | `#d6d6d3` | `#2e3a35` | borda fina dos cartões (decorativa) |
| `--borda` | `#6b6b6b` | `#7d8a84` | borda de campos, de barras e do estado vazio (pelo menos 3:1) |
| `--cartao-hover` | `#fafbfa` | `#222c28` | cartão-link com o mouse em cima |
| `--primaria` | `#1b6e3a` | `#1d7340` | fundo verde: botão principal, cartão do saldo, selo, faixa de entrada |
| `--primaria-escura` | `#14532b` | `#165c33` | botão principal no hover |
| `--primaria-texto` | `#1b6e3a` | `#6fd09a` | texto verde: marca, links, entradas, XP, contorno da resposta certa |
| `--perigo` | `#b3261e` | `#c2362c` | fundo vermelho: botão de excluir, saldo negativo, faixa de gasto |
| `--perigo-escura` | `#8f1e18` | `#a12a21` | botão de excluir no hover |
| `--perigo-texto` | `#b3261e` | `#ff8f85` | texto vermelho: gastos, erros, borda do campo com erro |
| `--foco` | `#1a5fb4` | `#7ab3f5` | contorno de foco, missão em andamento, pergunta nova |
| `--foco-fundo` | `#eef3fb` | `#1c2a3b` | alternativa do quiz marcada |
| `--sucesso-fundo` | `#e7f4ea` | `#173323` | aviso de sucesso, meta concluída, selo de XP |
| `--sucesso-borda` | `#b9dcc3` | `#2c5a3e` | borda da meta concluída |
| `--erro-fundo` | `#fbeaea` | `#3a1d1b` | aviso de erro, alerta de inativos, confirmação de exclusão |

Texto branco (`--texto-sobre-cor`) sobre `--primaria` e `--perigo` passa de 5:1 nos dois temas. Cor nova entra no `tokens.css` com a versão clara e a escura, e o par dela vai para a lista do teste de contraste.

## 4. Tipografia
- **Família:** fonte do sistema (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`). Sem webfont.
- **Base:** 16px, altura de linha 1,5.
- **Escala:**
  - número de destaque (saldo, XP em Missões, alunos ativos): 2,5rem;
  - título da página (h1): 1,5rem;
  - número de indicador: 1,4rem;
  - título de cartão: 1,1rem;
  - rótulo de seção: 0,8rem, negrito, MAIÚSCULAS, espaçamento 0,06em, cor `--texto-suave`;
  - item do menu do rodapé: 0,75rem.
- **Pesos:** 400 no texto, 600 em rótulos de campo e botões, 700 na marca, nos números e no item ativo do menu.

## 5. Forma, espaço e profundidade
- **Raio:** 8px em cartões, campos, botões e avisos; selos em pílula.
- **Espaçamento:** múltiplos de 0,25rem. Padding de cartão 1rem. Distância entre cartões 0,75rem. Padding da página 1rem.
- **Profundidade:** sem sombras. A página tem fundo `--suave`; os cartões têm fundo `--fundo` (branco no claro) e borda fina `--divisoria`.
- **Faixa de 6px na borda esquerda:** só nos itens de lista, para o tipo ou o status: lançamento (verde entrada, vermelho gasto), missão (azul em andamento, verde concluída, cinza bloqueada), pergunta do quiz (azul nova, verde acertou, vermelho errou), turma (verde) e avisos. O status também vai em texto.

## 6. Componentes
- **Topo:** fundo `--fundo`. À esquerda a marca "EducaInvest" em verde e o apelido com o perfil ("Ana · Aluno", que encolhe com reticências no celular). À direita, o aluno tem o atalho "Quiz" (ícone + texto) e "Sair"; o professor tem "Turmas" e "Sair". Login e cadastro não têm topo: a marca aparece grande, num quadrado verde com o ícone de gráfico.
- **Menu do aluno:** barra fixa no rodapé com 5 itens (Início, Lançamentos, Novo, Missões, Metas), ícone + texto. "Novo" é um círculo verde. O item atual fica verde, em negrito e com fundo claro no ícone. A partir de 48rem a barra vira uma linha abaixo do topo.
- **Botão principal:** fundo verde, texto branco 600, altura mínima de 44px. Versão larga (100%) para a ação principal da tela.
- **Botão de perigo:** fundo vermelho (excluir). Versão de contorno vermelho para "Excluir lançamento".
- **Botão secundário:** contorno verde de 2px com fundo `--fundo` (atalhos de aporte, "Cancelar").
- **Voltar:** seta à esquerda do título nas telas de formulário, quiz e turma.
- **Campo de formulário:** rótulo em negrito acima, campo com 100% de largura, borda `--borda`, altura de 44px. Com erro, a borda fica vermelha de 2px e a mensagem aparece em vermelho, embaixo do campo. Valores em reais usam um campo maior (1,6rem, negrito).
- **Botões de escolha (funcionam sem JavaScript):** rádios com cara de botão. Tipo do lançamento em dois botões (Gasto em vermelho, Entrada em verde), categoria em chips (o marcado fica escuro) e alternativas do quiz em cartões com a letra num círculo. O CSS (`:has`) mostra só as categorias do tipo marcado.
- **Barra de progresso:** `<progress>` com trilho claro e preenchimento verde; azul na missão em andamento; branca sobre cartão colorido.
- **Aviso (flash):** fundo claro e faixa esquerda de 6px: verde para sucesso, vermelha para erro.
- **Cartão de destaque:** verde, texto branco, número grande (saldo do aluno, nível em Missões, alunos ativos no painel da turma). Dentro dele o anel de foco é branco, porque o azul some sobre o verde. O saldo negativo pinta o cartão de vermelho e diz "Você gastou mais do que entrou."
- **Indicador:** cartão `--fundo` com rótulo em maiúsculas, número grande e uma dica curta, em grade de 2 colunas.
- **Selo:** pílula verde clara com "+50 XP", ou verde cheia com "Concluída" e o ícone de visto.
- **Estado vazio:** caixa com borda tracejada, frase em negrito, dica e o botão que resolve.
- **Código da turma:** monoespaçado, negrito, verde, com letras espaçadas; no convite, numa caixa tracejada.

## 7. Telas
1. **Login e cadastro:** marca grande, campos num cartão e botão largo. No cadastro, "Sou aluno" e "Sou professor" no topo (a opção atual cheia, a outra só com contorno); o aluno informa o código da turma e marca a autorização de uso dos dados (obrigatória).
2. **Início do aluno:** "Olá, Ana!", cartão verde do saldo (entradas e gastos embaixo, botão "Registrar gasto"), indicadores de sequência (com as 7 marcas dos últimos dias) e de nível (com a barra do nível), cartão da missão em andamento ("4 de 7 · Ver missões") e cartão da meta em andamento (nome e porcentagem, barra, "faltam R$ …"). Sem meta, o estado vazio "Crie sua primeira meta".
3. **Lançamentos:** "+ Novo", totais de entradas e gastos, busca com lupa e a lista "Recentes · toque para editar". O cartão inteiro abre a edição. Categorias de entrada: Mesada, Trabalho/bico, Benefício, Outras entradas. De gasto: Alimentação, Transporte, Lazer, Compras, Estudos, Outras saídas.
4. **Novo e editar lançamento:** tipo, valor grande, categoria em chips, descrição opcional (até 140 caracteres) e data. "Registrar gasto · +10 XP" ou "Registrar entrada · +10 XP". Na edição, "Salvar alterações", "Excluir lançamento" (com confirmação) e "Editar não rende XP."
5. **Missões:** cartão verde com nível, XP e barra; o XP de registros de hoje e o teto; a trilha (concluída, em andamento e bloqueada) e as conquistas em selos.
6. **Metas:** "+ Nova meta", resumo (guardado em todas as metas, em andamento e concluídas), metas em andamento com atalhos de aporte (R$ 5, R$ 10 e R$ 20, só os que cabem no que falta) e "Outro valor", e as concluídas separadas, com selo.
7. **Quiz:** XP do quiz hoje, perguntas por tema com faixa de status e, na pergunta, as alternativas em cartões. Depois de responder, a certa e a escolhida ficam marcadas e o resultado traz a explicação.
8. **Turmas do professor:** cada turma com o número de alunos e o código, e o cartão "Criar turma".
9. **Turma:** cartão verde com os ativos nos últimos 7 dias, XP médio e missões; "Precisa de atenção" com quem não ganhou XP nos últimos 7 dias; ranking por XP com barra; turma por nível; convite com o código. **Sem valores em reais e sem e-mail.**

## 7a. Movimento
Os padrões vêm do transitions.dev (skills `transitions-dev` e `transitions-polish`). O CSS fica em `app/static/css/movimento.css`; o JS, em `app/static/js/` (`movimento.js`, `contador.js` e `direcao.js`). O movimento completo fica dentro de `@media (prefers-reduced-motion: no-preference)`. Quem pede menos movimento recebe a versão suave: o aviso aparecendo, a troca de cor dos botões e um esmaecimento de 150ms entre páginas, sem deslocamento, escala, salto, confete nem barra se desenhando. Menos movimento não é zero.
- **Por que animar:** retorno ao toque, continuidade entre telas e comemoração de conquista. Nada anima "porque fica bonito". Ação repetida muitas vezes por dia anima pouco ou nada.
- **Curva e tempo** (tokens em `tokens.css`):
  - `--ease-out` é `cubic-bezier(0.23, 1, 0.32, 1)`: começa rápido e assenta devagar. Nunca `ease-in` em interface.
  - Toque: 160ms. Troca de cor: 150ms. Troca de página: 240ms (abaixo de 300ms, porque a página fica inerte durante a troca). Aviso: 200ms. Barra: 280ms.
  - Escala do transitions.dev: escalonar 40ms, tremida 80ms por trecho, fechar 150ms, abrir e deslizar 250ms, toast 350ms, ênfase 500ms; `--ease-mola` só em entrada (check, contador, escolha marcada), nunca em saída.
  - A comemoração é a exceção: até ~1,4s, uma vez só.
- **O que anima:**
  - **Troca de página:** `@view-transition { navigation: auto; }`. O topo e o menu ficam parados; o conteúdo sai num fade e entra subindo 8px. Onde o navegador não suporta, a página só carrega normal.
  - **Troca de página com direção** (`direcao.js`): ir para a direita no menu ou entrar num detalhe desliza 8px para a esquerda com desfoque de 3px; voltar desliza para o outro lado.
  - **Avisos:** entram descendo 6px. O de sucesso é um toast no rodapé, com check desenhado, e some da vista sozinho em 5s, só com CSS (o texto continua para o leitor de tela). O mouse em cima pausa, e um toque segura até o próximo toque (JS).
  - **Erro:** o campo com erro treme uma vez (80/60/80/60ms) e a mensagem entra junto.
  - **Escolhas:** o chip e a alternativa marcados assentam com mola; no Gasto/Entrada, uma pílula desliza até a opção (JS).
  - **Painel:** as marcas da sequência acendem em cascata; se o XP subiu desde a última visita neste aparelho, o número rola num tambor 3D e a barra enche desde onde estava (JS, `localStorage`).
  - **Quiz:** enunciado e alternativas entram em cascata; depois de responder, a certa assenta e a errada treme.
  - **Conquista** (missão, nível, meta concluída): o cartão verde dá um pequeno salto, o troféu balança e um confete de CSS cai uma vez.
  - **Toque:** botões, chips e alternativas afundam (`scale(.97)`); cartões-link e ícones do menu afundam menos (`scale(.985)` e `scale(.95)`).
  - **Barras:** se desenham da esquerda com `clip-path`. O navegador não anima o preenchimento do `<progress>`.
- **O que não anima:**
  - layout (`width`, `height`, `margin`, `top`);
  - nada parte de `scale(0)` e nada fica em loop;
  - nenhuma informação vem só do movimento;
  - nada só para chamar atenção em tela frequente: a marca de hoje na sequência não pulsa;
  - hover de cartão só com mouse (`@media (hover: hover) and (pointer: fine)`), porque no celular o toque deixa o hover preso.

## 8. Faça e não faça
**Faça**
- Uma ação principal por tela, bem visível.
- Estados vazio, erro e sucesso desenhados para cada lista e cada formulário.
- Números de dinheiro e XP grandes e fáceis de ler.
- Gamificação por texto e barra de progresso: nível, sequência e "+20 XP".

**Não faça**
- Gradientes, sombras fortes, glassmorphism, fundo escuro com neon, ilustrações 3D genéricas.
- Gráfico de pizza ou de linha (precisa de JavaScript ou de muita gambiarra em CSS).
- Mostrar valores em reais ou e-mail do aluno nas telas do professor.
- Menu hambúrguer, abas, modais ou qualquer coisa que só funcione com JavaScript.
- Textos em inglês ou jargão financeiro sem explicação.

## 9. Prompt sugerido
> Desenhe telas de celular (375px) de um app web de finanças gamificado para jovens brasileiros de 16 a 24 anos, seguindo o DESIGN.md anexo.
> Comece pela tela inicial do aluno, pela tela de metas e pelo painel agregado da turma para o professor.
> Respeite as restrições da seção 2: HTML e CSS puros (JavaScript só como enfeite que pode faltar), sem framework, sem sombras e sem gradientes. Mantenha a paleta e os componentes descritos, e mostre também o estado vazio de cada tela.
