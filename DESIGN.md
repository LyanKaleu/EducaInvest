# DESIGN.md · EducaInvest

Guia visual do EducaInvest para gerar telas em ferramentas de design (Claude Design, Google Stitch, Gemini).
Descreve o visual que existe hoje em `app/static/css/app.css` (o do protótipo navegável, aplicado em 16/11/2026) e as restrições do código. A fonte da verdade continua sendo o `app.css`.
Se uma proposta nova for aprovada, atualize este arquivo junto com o CSS.

## 1. Produto e público
- **O que é:** app web de gestão financeira gamificada. O aluno registra entradas e gastos, guarda dinheiro em metas e ganha XP com missões. O professor acompanha a turma.
- **Quem usa:** jovens de 16 a 24 anos, quase sempre no **celular**, muitos no primeiro contato com controle de dinheiro. O professor usa mais no computador.
- **Tom:** amigável, direto e encorajador, sem infantilizar. Frases curtas em português do Brasil, falando com "você". Comemora conquistas ("Parabéns!") sem exagero. Nunca culpa o aluno por gastar.
- **Sensação desejada:** um app de banco simples misturado com o progresso de um jogo. Confiável no dinheiro, leve na gamificação.

## 2. Restrições técnicas (obrigatórias)
O design precisa caber nestas regras. Proposta que depende de algo fora delas não é implementável.
- **HTML renderizado no servidor (Jinja), sem JavaScript.** Nada de modal, drawer, carrossel, abas dinâmicas, tooltip, drag and drop, toast que some sozinho ou gráfico interativo. Toda ação é um link ou um formulário que recarrega a página.
- **CSS puro num arquivo só**, sem framework (sem Tailwind, sem Bootstrap) e sem fonte externa. Animação só em CSS e discreta, respeitando `prefers-reduced-motion`. Sem `style` inline: a política de segurança (CSP) bloqueia.
- **Gráficos:** só o que dá para fazer com HTML e CSS: `<progress>`, barras com largura em %, números grandes. Sem bibliotecas de gráfico.
- **Ícones:** SVG inline de traço, sempre acompanhados de texto. Nada de emoji. Nenhuma informação só no ícone.
- **Mobile-first:** tudo funciona em 375px de largura. O conteúdo fica numa coluna de no máximo 40rem (640px) centralizada, também no desktop.
- **Acessibilidade (WCAG AA):** contraste de pelo menos 4,5:1 para texto, foco do teclado sempre visível, área de toque de pelo menos 44px, e cor nunca é a única pista (o sinal "-" vai no valor, o status vai escrito).
- **Dinheiro:** formato `R$ 1.234,56`, números com algarismos tabulares. Saldo negativo aparece como `-R$ 10,50`.

## 3. Cores
Paleta curta. Verde é a cor da marca e do dinheiro que entra; vermelho é gasto, erro e excluir; azul é foco e "em andamento".

| Token | Hex | Uso |
|---|---|---|
| `--texto` | `#1a1a1a` | texto principal |
| `--texto-suave` | `#555555` | rótulos, dicas e itens inativos do menu |
| `--fundo` | `#ffffff` | cartões e campos |
| `--suave` | `#f3f4f2` | fundo da página e trilho das barras |
| `--divisoria` | `#d6d6d3` | borda fina dos cartões (decorativa) |
| `--borda` | `#6b6b6b` | borda de campos, de barras e do estado vazio (contraste 5,3:1) |
| `--primaria` | `#1b6e3a` | marca, botão principal, cartão do saldo, entradas, XP, concluído |
| `--perigo` | `#b3261e` | gastos, saldo negativo, erros, botão de excluir |
| `--foco` | `#1a5fb4` | contorno de foco, missão em andamento, pergunta nova |
| `--sucesso-fundo` | `#e7f4ea` | aviso de sucesso, meta concluída, selo de XP |
| `--erro-fundo` | `#fbeaea` | aviso de erro, alerta de inativos, confirmação de exclusão |

Texto branco sobre `--primaria`, `--perigo` e `--foco` passa de 6:1.

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
- **Profundidade:** sem sombras. A página tem fundo `--suave`; os cartões são brancos com borda fina `--divisoria`.
- **Faixa de 6px na borda esquerda:** só nos itens de lista, para o tipo ou o status: lançamento (verde entrada, vermelho gasto), missão (azul em andamento, verde concluída, cinza bloqueada), pergunta do quiz (azul nova, verde acertou, vermelho errou), turma (verde) e avisos. O status também vai em texto.

## 6. Componentes
- **Topo:** fundo branco. À esquerda a marca "EducaInvest" em verde e o apelido com o perfil ("Ana · Aluno", que encolhe com reticências no celular). À direita, o aluno tem o atalho "Quiz" (ícone + texto) e "Sair"; o professor tem "Turmas" e "Sair". Login e cadastro não têm topo: a marca aparece grande, num quadrado verde com o ícone de gráfico.
- **Menu do aluno:** barra fixa no rodapé com 5 itens (Início, Lançamentos, Novo, Missões, Metas), ícone + texto. "Novo" é um círculo verde. O item atual fica verde, em negrito e com fundo claro no ícone. A partir de 48rem a barra vira uma linha abaixo do topo.
- **Botão principal:** fundo verde, texto branco 600, altura mínima de 44px. Versão larga (100%) para a ação principal da tela.
- **Botão de perigo:** fundo vermelho (excluir). Versão de contorno vermelho para "Excluir lançamento".
- **Botão secundário:** contorno verde de 2px com fundo branco (atalhos de aporte, "Cancelar").
- **Voltar:** seta à esquerda do título nas telas de formulário, quiz e turma.
- **Campo de formulário:** rótulo em negrito acima, campo com 100% de largura, borda `--borda`, altura de 44px. Com erro, a borda fica vermelha de 2px e a mensagem aparece em vermelho, embaixo do campo. Valores em reais usam um campo maior (1,6rem, negrito).
- **Botões de escolha (sem JavaScript):** rádios com cara de botão. Tipo do lançamento em dois botões (Gasto em vermelho, Entrada em verde), categoria em chips (o marcado fica escuro) e alternativas do quiz em cartões com a letra num círculo. O CSS (`:has`) mostra só as categorias do tipo marcado.
- **Barra de progresso:** `<progress>` com trilho claro e preenchimento verde; azul na missão em andamento; branca sobre cartão colorido.
- **Aviso (flash):** fundo claro e faixa esquerda de 6px: verde para sucesso, vermelha para erro.
- **Cartão de destaque:** verde, texto branco, número grande (saldo do aluno, nível em Missões, alunos ativos no painel da turma). O saldo negativo pinta o cartão de vermelho e diz "Você gastou mais do que entrou."
- **Indicador:** cartão branco com rótulo em maiúsculas, número grande e uma dica curta, em grade de 2 colunas.
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
- Menu hambúrguer, abas, modais ou qualquer coisa que dependa de clique sem recarregar a página.
- Textos em inglês ou jargão financeiro sem explicação.

## 9. Prompt sugerido
> Desenhe telas de celular (375px) de um app web de finanças gamificado para jovens brasileiros de 16 a 24 anos, seguindo o DESIGN.md anexo.
> Comece pela tela inicial do aluno, pela tela de metas e pelo painel agregado da turma para o professor.
> Respeite as restrições da seção 2: HTML e CSS puros, sem JavaScript, sem framework, sem sombras e sem gradientes. Mantenha a paleta e os componentes descritos, e mostre também o estado vazio de cada tela.
