@AGENTS.md
@INVARIANTES.md
@ESTADO.md

# Artefatos a cada etapa (só Claude)
- Ao avançar uma etapa (exploração, plano, implementação, revisão), publique um artefato visual: mapa mental, especificação, fluxo, diagrama ou checklist de verificação. Atualize o mesmo artefato da tarefa em vez de criar um por etapa e cite o link no plano e no PR.
- Ao implementar, carregue de fato as skills do AGENTS.md (Skill tool), não só cite o nome.
- No início da sessão, confira o ESTADO.md; ao fechar o PR, atualize o ESTADO.md se a fase ou o próximo passo mudou.

# Compact instructions
Ao compactar, preserve: arquivos modificados, a última saída do `bash gate.sh` DEPOIS da última edição,
as decisões de design da sessão e as tentativas rejeitadas (só o motivo, sem o código).
