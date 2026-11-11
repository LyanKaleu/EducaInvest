# DESIGN.md · EducaInvest

Guia visual do EducaInvest para gerar telas em ferramentas de design (Claude Design, Google Stitch, Gemini).
Descreve o visual que existe hoje em `app/static/css/app.css` e as restrições do código. A fonte da verdade continua sendo o `app.css`.
Se uma proposta nova for aprovada, atualize este arquivo junto com o CSS.

## 1. Produto e público
- **O que é:** app web de gestão financeira gamificada. O aluno registra entradas e gastos, guarda dinheiro em metas e ganha XP com missões. O professor acompanha a turma.
- **Quem usa:** jovens de 16 a 24 anos, quase sempre no **celular**, muitos no primeiro contato com controle de dinheiro. O professor usa mais no computador.
- **Tom:** amigável, direto e encorajador, sem infantilizar. Frases curtas em português do Brasil, falando com "você". Comemora conquistas ("Parabéns!") sem exagero. Nunca culpa o aluno por gastar.
- **Sensação desejada:** um app de banco simples misturado com o progresso de um jogo. Confiável no dinheiro, leve na gamificação.

## 2. Restrições técnicas (obrigatórias)
O design precisa caber nestas regras. Proposta que depende de algo fora delas não é implementável.
- **HTML renderizado no servidor (Jinja), sem JavaScript.** Nada de modal, drawer, carrossel, abas dinâmicas, tooltip, drag and drop, toast que some sozinho ou gráfico interativo. Toda ação é um link ou um formulário que recarrega a página.
- **CSS puro num arquivo só**, sem framework (sem Tailwind, sem Bootstrap) e sem fonte externa. Animação só em CSS e discreta, respeitando `prefers-reduced-motion`.
- **Gráficos:** só o que dá para fazer com HTML e CSS: `<progress>`, barras com largura em %, números grandes. Sem bibliotecas de gráfico.
- **Ícones:** opcionais. Se usar, SVG inline simples ou emoji, sempre acompanhados de texto. Nenhuma informação só no ícone.
- **Mobile-first:** tudo funciona em 375px de largura. O conteúdo fica numa coluna de no máximo 40rem (640px) centralizada, também no desktop.
- **Acessibilidade (WCAG AA):** contraste de pelo menos 4,5:1 para texto, foco do teclado sempre visível, área de toque de pelo menos 44px, e cor nunca é a única pista (o sinal "-" vai no valor, o status vai escrito).
- **Dinheiro:** formato `R$ 1.234,56`, números com algarismos tabulares. Saldo negativo aparece como `-R$ 10,50`.

## 3. Cores
Paleta curta. Verde é a cor da marca e do dinheiro que entra; vermelho é gasto, erro e excluir; azul é foco e "em andamento".

| Token | Hex | Uso |
|---|---|---|
| `--texto` | `#1a1a1a` | texto principal |
| `--fundo` | `#ffffff` | fundo da página e dos campos |
| `--suave` | `#f3f4f2` | fundo dos cartões de lista (lançamento, missão, meta) |
| `--borda` | `#6b6b6b` | borda de campos e de indicadores (contraste 5,3:1) |
| `--primaria` | `#1b6e3a` | marca, barra do topo, botão principal, entradas, saldo positivo, XP, concluído |
| `--perigo` | `#b3261e` | gastos, saldo negativo, erros, botão de excluir |
| `--foco` | `#1a5fb4` | contorno de foco, missão ativa, meta em andamento |

Apoio: texto secundário `#555` (dicas e rótulos), descrição `#444`, aviso de sucesso com fundo `#e7f4ea`, aviso de erro com fundo `#fbeaea`.
Texto branco sobre `--primaria`, `--perigo` e `--foco` passa de 6:1.

## 4. Tipografia
- **Família:** fonte do sistema (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`). Sem webfont.
- **Base:** 16px, altura de linha 1,5.
- **Escala:**
  - saldo da tela inicial: 2,25rem, cor primária;
  - total de XP: 2rem;
  - título da página (h1): 1,5rem;
  - número de indicador: 1,4rem;
  - subtítulo (h2): 1,1 a 1,2rem;
  - rótulo de seção: 0,8rem, negrito, MAIÚSCULAS, espaçamento 0,06em, cor `#555`.
- **Pesos:** 400 no texto, 600 em rótulos de campo e botões, 700 na marca e no item ativo do menu.

## 5. Forma, espaço e profundidade
- **Raio:** 8px em tudo (cartões, campos, botões, avisos).
- **Espaçamento:** múltiplos de 0,25rem. Padding de cartão 0,75rem × 1rem. Distância entre cartões 0,75rem. Padding da página 1rem.
- **Profundidade:** sem sombras. A hierarquia vem do fundo `--suave`, de bordas e de uma **faixa de 6px na borda esquerda** que indica o tipo ou o status do item.

## 6. Componentes
- **Barra do topo:** fundo verde, links brancos. À esquerda a marca "EducaInvest" e o apelido com o perfil ("Ana · Aluno"). À direita o menu: aluno tem Início, Lançamentos, Novo, Missões, Metas e Sair; professor tem Turmas e Sair. O item atual fica em negrito com sublinhado grosso. No celular o menu quebra em linhas, não vira hambúrguer.
- **Botão principal:** fundo verde, texto branco 600, altura mínima de 44px. Versão larga (100%) para a ação principal da tela ("Registrar gasto").
- **Botão de perigo:** igual, com fundo vermelho (excluir).
- **Botão secundário:** contorno verde de 2px com fundo branco.
- **Campo de formulário:** rótulo em negrito acima, campo com 100% de largura, borda `--borda`, altura de 44px. Dica em `#555` abaixo do rótulo. Com erro, a borda fica vermelha de 2px e a mensagem aparece em vermelho, embaixo do campo.
- **Opção (rádio):** rádio de 20px na cor primária, com o texto ao lado, em linha.
- **Aviso (flash):** faixa com fundo claro e borda esquerda de 6px: verde para sucesso, vermelha para erro.
- **Cartão de lançamento:** fundo `--suave` e faixa esquerda verde (entrada) ou vermelha (gasto). Mostra categoria, data e descrição à esquerda, e o valor colorido à direita.
- **Cartão de missão:** faixa cinza (bloqueada), azul (ativa) ou verde (concluída). Título, descrição, recompensa ("+20 XP") e barra de progresso verde ("2 de 5").
- **Cartão de meta:** faixa azul (em andamento) ou verde (concluída, com selo "Concluída"). Nome, "R$ 120,00 de R$ 300,00 · 40%", barra de progresso e formulário de aporte em linha (campo + botão "Guardar").
- **Indicador:** caixa com borda fina, rótulo em maiúsculas, número grande e uma dica curta. Fica em grade de 2 colunas no celular.
- **Código da turma:** monoespaçado, 1,1rem, negrito, com letras espaçadas.

## 7. Telas
Telas existentes (redesenhe mantendo o conteúdo):
1. **Login e cadastro:** escolha entre "Sou aluno" e "Sou professor" no topo do cadastro (a opção atual cheia, a outra só com contorno). O aluno informa o código da turma e marca a autorização de uso dos dados (obrigatória).
2. **Início do aluno:** "Olá, Ana!", saldo grande (com entradas e gastos embaixo), botão largo "Registrar gasto", dois indicadores (Sequência: "3 dias"; Nível 2 · Aprendiz: "140 XP, faltam 160 para o próximo"), cartão da missão em andamento e cartão da meta em andamento. Cada cartão tem um estado vazio ("Crie sua primeira meta").
3. **Lançamentos:** busca no topo e lista de cartões de entrada e gasto. Categorias de entrada: Mesada, Trabalho/bico, Benefício, Outras entradas. De gasto: Alimentação, Transporte, Lazer, Compras, Estudos, Outras saídas.
4. **Novo lançamento:** tipo (Gasto ou Entrada), valor, categoria, data e descrição opcional (até 140 caracteres).
5. **Missões:** total de XP e nível no topo, trilha de missões (bloqueada, ativa e concluída) e conquistas.
6. **Metas:** lista de metas com progresso e aporte, mais o botão "+ Nova meta".
7. **Turmas do professor:** lista de turmas e formulário para criar uma.
8. **Turma:** nome, código de acesso e lista de alunos (só o apelido).

Telas que ainda vão ser feitas:
9. **Painel agregado da turma (professor):** números da turma inteira, **sem valores em reais e sem e-mail**. Ex.: quantos alunos registraram na semana, missões concluídas, nível médio, distribuição por nível e uma lista de alunos com apelido, nível e sequência.
10. **Quiz (aluno):** uma pergunta de múltipla escolha por tela, botão "Responder" e, na tela seguinte, se acertou e a explicação da resposta, com o XP ganho.

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
