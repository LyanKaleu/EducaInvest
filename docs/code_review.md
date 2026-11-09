# Critérios de revisão de código

Usado pelo subagente `revisor` e por quem revisa PR. Compare o diff com a tarefa (Goal e Done when) e com o INVARIANTES.md.

## Reporte APENAS
1. **Corretude:** bug, caso de borda, condição de corrida, dinheiro fora de centavos, data fora de `hoje_no_piaui()`.
2. **Requisitos:** item do "Done when" que não foi implementado ou não tem teste.
3. **Invariantes:** violação de qualquer regra do INVARIANTES.md, inclusive alteração em CREATE TABLE existente (O1).
4. **Escopo:** arquivo alterado que a tarefa não pedia.
5. **Segurança:** rota sem perfil, acesso a dado de outro usuário, segredo no código, SQL montado com texto do usuário, e-mail exposto ao professor.
6. **Teste que não morde:** teste de correção que passaria mesmo sem a correção.

## NÃO reporte
- Preferência de estilo que o ruff já aceita.
- Abstração "para o futuro" (factory, interface com uma implementação só).
- Renomeação cosmética.
- Teste para caso que o domínio não permite.
- `try/except` defensivo sem um erro real a tratar.

## Formato
Uma linha por achado: `arquivo:linha · problema · por que importa · correção sugerida`.
Afirmação sem `arquivo:linha` é descartada. No máximo 15 linhas.
Se o diff está sólido, diga que está sólido. Não invente achados para parecer útil.
