# Desenvolvimento com IA: guia prático

## Sumário
1. Como pedir código com bom contexto
2. Revisando código gerado por IA
3. Armadilhas comuns
4. Fluxos que funcionam
5. Segurança e privacidade

## 1. Como pedir código com bom contexto

Um bom pedido tem, em ordem de importância:

- **Objetivo**: o que deve existir ao final e por quê.
- **Contexto técnico**: linguagem, versão, framework, estrutura de pastas, trechos relevantes.
- **Restrições**: bibliotecas permitidas ou proibidas, desempenho, compatibilidade, estilo.
- **Critério de aceite**: como saber que está pronto (testes, exemplos de entrada/saída).
- **Exemplo do estilo desejado**: um trecho existente do projeto vale mais que uma descrição.

Exemplo fraco: "faça um endpoint de login."
Exemplo forte: "FastAPI 0.11x, pydantic v2. Criar `POST /auth/login` que recebe email e senha, valida contra a tabela `users` (SQLAlchemy async, já existe em `app/models.py`), retorna JWT com expiração de 15 min. Sem novas dependências além de `pyjwt`. Incluir testes pytest para credenciais válidas, senha errada e usuário inexistente."

## 2. Revisando código gerado por IA

Leia como se fosse de um desenvolvedor júnior muito rápido e confiante:

- **Correção**: a lógica faz o que foi pedido? Bordas (vazio, nulo, limites, concorrência)?
- **APIs reais**: as funções e parâmetros existem na versão usada? Confira na documentação.
- **Segurança**: injeção (SQL, comando, prompt), validação de entrada, segredos, autorização e não só autenticação.
- **Erros**: exceções engolidas, falta de timeout/retry, mensagens que vazam detalhes internos.
- **Dependências**: pacotes novos são necessários, mantidos e confiáveis? Cuidado com nomes parecidos com pacotes legítimos.
- **Escopo**: o código fez só o pedido ou mexeu em coisas não solicitadas?
- **Testes**: testam comportamento real ou só repetem a implementação?

## 3. Armadilhas comuns

- Funções/métodos inexistentes ("alucinação de API").
- Código que passa nos testes escritos pela própria IA mas não resolve o problema real.
- Refatorações amplas e silenciosas que quebram comportamento.
- Excesso de abstração e código "enterprise" para problemas pequenos.
- Perda de contexto em conversas longas: reafirme requisitos importantes.
- Aceitar o primeiro resultado sem rodar.

## 4. Fluxos que funcionam

- **Spec → plano → implementação em passos → testes → revisão.**
- **Teste primeiro**: escreva (ou peça) os testes, confirme que falham, depois implemente.
- **Depuração**: forneça a mensagem de erro completa, o trecho relevante, o que já tentou e o resultado esperado. Peça hipóteses ordenadas por probabilidade e como confirmar cada uma antes de mudar o código.
- **Refatoração segura**: garanta testes existentes passando, mude uma coisa por vez, rode a cada passo.
- **Exploração de código desconhecido**: peça um mapa (entrada, fluxo principal, dependências) antes de mudar qualquer coisa.
- **Documentação**: gere a partir do código real e revise; não confie em descrições do que o código "deveria" fazer.

## 5. Segurança e privacidade

- Nunca incluir chaves, senhas, tokens ou dados pessoais em prompts.
- Verificar a política da empresa para uso de ferramentas de IA com código proprietário.
- Rodar código gerado e comandos sugeridos em ambiente isolado quando houver dúvida; ler antes de executar comandos destrutivos (`rm`, `DROP`, migrações).
- Aplicar o princípio do menor privilégio a qualquer ferramenta ou agente que execute ações.
