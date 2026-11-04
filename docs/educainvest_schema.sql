-- =====================================================================
-- EducaInvest - Gestão Financeira Gamificada
-- Modelo de dados do MVP (PostgreSQL 15+)
-- Convenções: valores em centavos (BIGINT); datas "do dia" no fuso
-- America/Fortaleza (Piauí); exclusão de aluno apaga seus dados (CASCADE).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. Acesso: usuários, turmas, matrículas (RF01, RF02)
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    perfil            TEXT        NOT NULL CHECK (perfil IN ('ALUNO', 'PROFESSOR')),
    apelido           TEXT        NOT NULL CHECK (char_length(btrim(apelido)) BETWEEN 2 AND 40),
    email             TEXT        NOT NULL CHECK (position('@' IN email) > 1),
    senha_hash        TEXT        NOT NULL,
    consentimento_em  TIMESTAMPTZ,            -- consentimento (menores de 18); regra a definir
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_usuarios_email ON usuarios (lower(email));

CREATE TABLE turmas (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    professor_id   BIGINT      NOT NULL REFERENCES usuarios (id),
    nome           TEXT        NOT NULL CHECK (char_length(btrim(nome)) BETWEEN 1 AND 60),
    codigo_acesso  TEXT        NOT NULL UNIQUE CHECK (codigo_acesso ~ '^[A-Z0-9]{6,8}$'),
    ativa          BOOLEAN     NOT NULL DEFAULT TRUE,
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (professor_id, nome)
);

-- aluno_id como PK: cada aluno pertence a uma única turma no MVP
CREATE TABLE matriculas (
    aluno_id   BIGINT      PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    turma_id   BIGINT      NOT NULL REFERENCES turmas (id),
    entrou_em  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_matriculas_turma ON matriculas (turma_id);

-- ---------------------------------------------------------------------
-- 2. Registro financeiro (RF03, RF04)
-- ---------------------------------------------------------------------
CREATE TABLE categorias (
    id    SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome  TEXT NOT NULL CHECK (char_length(btrim(nome)) > 0),
    tipo  TEXT NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    UNIQUE (nome, tipo),
    UNIQUE (id, tipo)            -- permite a FK composta de lancamentos
);

CREATE TABLE lancamentos (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id            BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    tipo                TEXT        NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    categoria_id        SMALLINT    NOT NULL,
    valor_centavos      BIGINT      NOT NULL CHECK (valor_centavos > 0),
    data_lancamento     DATE        NOT NULL
                        CHECK (data_lancamento <= (now() AT TIME ZONE 'America/Fortaleza')::date),
    descricao           TEXT        CHECK (descricao IS NULL OR char_length(descricao) <= 140),
    chave_idempotencia  UUID        NOT NULL,   -- gerada pelo cliente; evita duplicar em retry
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (aluno_id, chave_idempotencia),
    UNIQUE (aluno_id, id),                      -- alvo da FK composta de xp_eventos
    -- a categoria precisa ser do mesmo tipo do lançamento (entrada x saída)
    FOREIGN KEY (categoria_id, tipo) REFERENCES categorias (id, tipo)
);
CREATE INDEX ix_lancamentos_aluno_data ON lancamentos (aluno_id, data_lancamento DESC);

CREATE TABLE metas (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id             BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    nome                 TEXT        NOT NULL CHECK (char_length(btrim(nome)) BETWEEN 1 AND 60),
    valor_alvo_centavos  BIGINT      NOT NULL CHECK (valor_alvo_centavos > 0),
    prazo                DATE,
    criada_em            TIMESTAMPTZ NOT NULL DEFAULT now(),
    concluida_em         TIMESTAMPTZ,
    CHECK (prazo IS NULL OR prazo >= (criada_em AT TIME ZONE 'America/Fortaleza')::date)
);
CREATE INDEX ix_metas_aluno ON metas (aluno_id);

-- Aporte separado do saldo (decisão em aberto: descontar ou não do saldo)
CREATE TABLE aportes_meta (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meta_id             BIGINT      NOT NULL REFERENCES metas (id) ON DELETE CASCADE,
    valor_centavos      BIGINT      NOT NULL CHECK (valor_centavos > 0),
    chave_idempotencia  UUID        NOT NULL,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (meta_id, chave_idempotencia)
);

-- ---------------------------------------------------------------------
-- 3. Missões (RF05)
-- ---------------------------------------------------------------------
CREATE TABLE missoes (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo          TEXT     NOT NULL UNIQUE CHECK (codigo ~ '^[A-Z0-9_]+$'),
    titulo          TEXT     NOT NULL,
    descricao       TEXT     NOT NULL,
    tipo_regra      TEXT     NOT NULL
                    CHECK (tipo_regra IN ('QTD_LANCAMENTOS', 'APORTE_META', 'QUIZ_CONCLUIDO')),
    parametros      JSONB    NOT NULL DEFAULT '{}'::jsonb,  -- ex.: {"tipo":"SAIDA"}
    meta_progresso  INT      NOT NULL CHECK (meta_progresso > 0),  -- "3" em "2 de 3"
    xp_recompensa   INT      NOT NULL CHECK (xp_recompensa > 0),
    requisito_id    SMALLINT REFERENCES missoes (id),              -- pré-requisito (trilha)
    ordem           SMALLINT NOT NULL UNIQUE,
    ativa           BOOLEAN  NOT NULL DEFAULT TRUE,
    CHECK (requisito_id IS NULL OR requisito_id <> id)
);

-- A linha só existe quando a missão é desbloqueada para o aluno.
-- A PK (aluno_id, missao_id) impede concluir/pontuar a mesma missão duas vezes.
CREATE TABLE missoes_aluno (
    aluno_id         BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    missao_id        SMALLINT    NOT NULL REFERENCES missoes (id),
    status           TEXT        NOT NULL DEFAULT 'ATIVA' CHECK (status IN ('ATIVA', 'CONCLUIDA')),
    progresso_atual  INT         NOT NULL DEFAULT 0 CHECK (progresso_atual >= 0),
    iniciada_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    concluida_em     TIMESTAMPTZ,
    PRIMARY KEY (aluno_id, missao_id),
    CHECK ((status = 'CONCLUIDA') = (concluida_em IS NOT NULL))
);

-- ---------------------------------------------------------------------
-- 4. Quizzes (RF06). No MVP, cada quiz curto é uma pergunta.
-- ---------------------------------------------------------------------
CREATE TABLE quiz_perguntas (
    id             SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tema           TEXT     NOT NULL CHECK (tema IN ('JUROS', 'CREDITO', 'ORCAMENTO', 'INFLACAO')),
    enunciado      TEXT     NOT NULL,
    explicacao     TEXT     NOT NULL,
    xp_recompensa  INT      NOT NULL CHECK (xp_recompensa > 0),
    ativa          BOOLEAN  NOT NULL DEFAULT TRUE
);

CREATE TABLE quiz_alternativas (
    id           INT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pergunta_id  SMALLINT NOT NULL REFERENCES quiz_perguntas (id) ON DELETE CASCADE,
    texto        TEXT     NOT NULL,
    correta      BOOLEAN  NOT NULL DEFAULT FALSE,
    UNIQUE (id, pergunta_id)
);
-- no máximo uma alternativa correta por pergunta
CREATE UNIQUE INDEX ux_quiz_uma_correta ON quiz_alternativas (pergunta_id) WHERE correta;

-- PK (aluno_id, pergunta_id): uma única resposta por pergunta (a primeira vale)
CREATE TABLE quiz_respostas (
    aluno_id        BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    pergunta_id     SMALLINT    NOT NULL REFERENCES quiz_perguntas (id),
    alternativa_id  INT         NOT NULL,
    correta         BOOLEAN     NOT NULL,
    respondida_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (aluno_id, pergunta_id),
    -- a alternativa escolhida precisa pertencer à pergunta respondida
    FOREIGN KEY (alternativa_id, pergunta_id) REFERENCES quiz_alternativas (id, pergunta_id)
);

-- ---------------------------------------------------------------------
-- 5. Gamificação: XP (livro-razão), níveis e conquistas (RF07)
-- ---------------------------------------------------------------------
CREATE TABLE niveis (
    nivel      SMALLINT PRIMARY KEY CHECK (nivel >= 1),
    nome       TEXT     NOT NULL,
    xp_minimo  INT      NOT NULL UNIQUE CHECK (xp_minimo >= 0)
);

-- Somente inserções: o XP nunca diminui. Cada evento aponta para UMA origem.
CREATE TABLE xp_eventos (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id          BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    pontos            INT         NOT NULL CHECK (pontos > 0),
    lancamento_id     BIGINT,
    missao_id         SMALLINT,
    quiz_pergunta_id  SMALLINT,
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT now(),
    dia_ref           DATE GENERATED ALWAYS AS
                      ((criado_em AT TIME ZONE 'America/Fortaleza')::date) STORED,
    CHECK (num_nonnulls(lancamento_id, missao_id, quiz_pergunta_id) = 1),
    -- FKs compostas: a origem precisa ser do mesmo aluno (ignoradas quando a coluna é NULL)
    FOREIGN KEY (aluno_id, lancamento_id)    REFERENCES lancamentos   (aluno_id, id),
    FOREIGN KEY (aluno_id, missao_id)        REFERENCES missoes_aluno (aluno_id, missao_id),
    FOREIGN KEY (aluno_id, quiz_pergunta_id) REFERENCES quiz_respostas (aluno_id, pergunta_id),
    -- uma origem só pontua uma vez (NULLs não colidem entre si)
    UNIQUE (aluno_id, lancamento_id),
    UNIQUE (aluno_id, missao_id),
    UNIQUE (aluno_id, quiz_pergunta_id)
);
CREATE INDEX ix_xp_aluno_dia ON xp_eventos (aluno_id, dia_ref);

CREATE TABLE conquistas (
    id         SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo     TEXT NOT NULL UNIQUE CHECK (codigo ~ '^[A-Z0-9_]+$'),
    titulo     TEXT NOT NULL,
    descricao  TEXT NOT NULL
);

CREATE TABLE conquistas_aluno (
    aluno_id      BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    conquista_id  SMALLINT    NOT NULL REFERENCES conquistas (id),
    obtida_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (aluno_id, conquista_id)
);

-- ---------------------------------------------------------------------
-- 6. Views derivadas (nada disso é armazenado)
-- ---------------------------------------------------------------------
-- Saldo, XP total, nível: calculados, nunca gravados em coluna.
CREATE VIEW vw_saldo_aluno AS
SELECT aluno_id,
       COALESCE(SUM(CASE tipo WHEN 'ENTRADA' THEN valor_centavos ELSE -valor_centavos END), 0) AS saldo_centavos
FROM lancamentos
GROUP BY aluno_id;

CREATE VIEW vw_xp_aluno AS
WITH totais AS (
    SELECT u.id AS aluno_id, COALESCE(SUM(x.pontos), 0)::INT AS xp_total
    FROM usuarios u
    LEFT JOIN xp_eventos x ON x.aluno_id = u.id
    WHERE u.perfil = 'ALUNO'
    GROUP BY u.id
)
SELECT t.aluno_id,
       t.xp_total,
       (SELECT n.nivel FROM niveis n
         WHERE n.xp_minimo <= t.xp_total
         ORDER BY n.nivel DESC LIMIT 1) AS nivel
FROM totais t;

-- Painel do professor (RF08): somente agregados, sem valores em reais.
-- "Aluno ativo" = teve XP nos últimos 7 dias (definição a confirmar).
CREATE VIEW vw_painel_turma AS
SELECT t.id AS turma_id,
       t.professor_id,
       t.nome AS turma,
       (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id) AS qtd_alunos,
       (SELECT COALESCE(ROUND(AVG(v.xp_total), 1), 0)
          FROM matriculas m JOIN vw_xp_aluno v ON v.aluno_id = m.aluno_id
         WHERE m.turma_id = t.id) AS xp_medio,
       (SELECT COUNT(*)
          FROM matriculas m
          JOIN missoes_aluno ma ON ma.aluno_id = m.aluno_id AND ma.status = 'CONCLUIDA'
         WHERE m.turma_id = t.id) AS missoes_concluidas,
       (SELECT COUNT(DISTINCT x.aluno_id)
          FROM matriculas m JOIN xp_eventos x ON x.aluno_id = m.aluno_id
         WHERE m.turma_id = t.id
           AND x.dia_ref >= (now() AT TIME ZONE 'America/Fortaleza')::date - 6) AS alunos_ativos_7d
FROM turmas t;

-- ---------------------------------------------------------------------
-- 7. Dados iniciais (valores de XP são PLACEHOLDERS a definir pelo grupo)
-- ---------------------------------------------------------------------
INSERT INTO categorias (nome, tipo) VALUES
    ('Mesada', 'ENTRADA'), ('Trabalho/bico', 'ENTRADA'), ('Benefício', 'ENTRADA'),
    ('Outras entradas', 'ENTRADA'),
    ('Alimentação', 'SAIDA'), ('Transporte', 'SAIDA'), ('Lazer', 'SAIDA'),
    ('Compras', 'SAIDA'), ('Estudos', 'SAIDA'), ('Outras saídas', 'SAIDA');

INSERT INTO niveis (nivel, nome, xp_minimo) VALUES
    (1, 'Iniciante', 0), (2, 'Aprendiz', 100), (3, 'Organizado', 300);

INSERT INTO missoes (codigo, titulo, descricao, tipo_regra, parametros, meta_progresso, xp_recompensa, requisito_id, ordem)
VALUES ('REG_3_GASTOS', 'Primeiros passos', 'Registre 3 gastos.',
        'QTD_LANCAMENTOS', '{"tipo":"SAIDA"}', 3, 30, NULL, 1);
INSERT INTO missoes (codigo, titulo, descricao, tipo_regra, parametros, meta_progresso, xp_recompensa, requisito_id, ordem)
VALUES ('REG_7_LANCAMENTOS', 'Hábito em construção', 'Registre 7 lançamentos (entradas ou saídas).',
        'QTD_LANCAMENTOS', '{}', 7, 50,
        (SELECT id FROM missoes WHERE codigo = 'REG_3_GASTOS'), 2);

COMMIT;
