"""Testes das regras de cadastro, login e senha (RF01, RN-04, RN-05, RNF04): só o service."""

import pytest
from werkzeug.security import generate_password_hash

# Importa o MÓDULO (que já existe) e não as funções: enquanto elas não existirem,
# cada teste falha sozinho, em vez de quebrar a coleta do arquivo inteiro.
from app.services import auth_service
from app.services.erros import ErroValidacao


@pytest.fixture
def form_aluno() -> dict[str, str]:
    return {
        "apelido": "Gabriel",
        "email": "gabriel@escola.br",
        "senha": "senha-segura-123",
        "codigo_turma": "ABC234",
        "consentimento": "sim",
    }


@pytest.fixture
def form_professor() -> dict[str, str]:
    return {
        "apelido": "Prof. Ana",
        "email": "ana@escola.br",
        "senha": "senha-segura-123",
    }


def erros_aluno(
    form: dict[str, str], **alteracoes: str | None
) -> dict[str, str]:
    with pytest.raises(ErroValidacao) as excinfo:
        auth_service.validar_cadastro_aluno({**form, **alteracoes})
    return excinfo.value.erros


# ---------------------------------------------------------------------------
# Cadastro do aluno: caminho feliz e normalização
# ---------------------------------------------------------------------------


def test_cadastro_de_aluno_valido_devolve_dados_normalizados(
    form_aluno: dict[str, str],
) -> None:
    dados = auth_service.validar_cadastro_aluno(form_aluno)

    assert dados == {
        "apelido": "Gabriel",
        "email": "gabriel@escola.br",
        "senha": "senha-segura-123",
        "codigo_turma": "ABC234",
    }


def test_email_e_guardado_em_minusculas_e_sem_espacos(
    form_aluno: dict[str, str],
) -> None:
    dados = auth_service.validar_cadastro_aluno(
        {**form_aluno, "email": "  Gabriel@Escola.BR "}
    )

    assert dados["email"] == "gabriel@escola.br"


def test_codigo_da_turma_e_aceito_em_minusculas(
    form_aluno: dict[str, str],
) -> None:
    dados = auth_service.validar_cadastro_aluno(
        {**form_aluno, "codigo_turma": " abc234 "}
    )

    assert dados["codigo_turma"] == "ABC234"


def test_apelido_tem_espacos_das_pontas_removidos(
    form_aluno: dict[str, str],
) -> None:
    dados = auth_service.validar_cadastro_aluno(
        {**form_aluno, "apelido": "  Gabriel  "}
    )

    assert dados["apelido"] == "Gabriel"


def test_senha_nao_tem_espacos_removidos(form_aluno: dict[str, str]) -> None:
    dados = auth_service.validar_cadastro_aluno(
        {**form_aluno, "senha": " senha com espaço "}
    )

    assert dados["senha"] == " senha com espaço "


# ---------------------------------------------------------------------------
# Cadastro do aluno: bordas
# ---------------------------------------------------------------------------


def test_apelido_com_2_caracteres_e_aceito(form_aluno: dict[str, str]) -> None:
    assert (
        auth_service.validar_cadastro_aluno({**form_aluno, "apelido": "Bê"})[
            "apelido"
        ]
        == "Bê"
    )


def test_apelido_com_1_caractere_e_recusado(
    form_aluno: dict[str, str],
) -> None:
    assert erros_aluno(form_aluno, apelido="B") == {
        "apelido": "Informe um apelido de 2 a 40 caracteres."
    }


def test_apelido_com_40_caracteres_e_aceito(
    form_aluno: dict[str, str],
) -> None:
    assert (
        len(
            auth_service.validar_cadastro_aluno(
                {**form_aluno, "apelido": "a" * 40}
            )["apelido"]
        )
        == 40
    )


def test_apelido_com_41_caracteres_e_recusado(
    form_aluno: dict[str, str],
) -> None:
    assert "apelido" in erros_aluno(form_aluno, apelido="a" * 41)


def test_senha_com_8_caracteres_e_aceita(form_aluno: dict[str, str]) -> None:
    assert (
        auth_service.validar_cadastro_aluno(
            {**form_aluno, "senha": "12345678"}
        )["senha"]
        == "12345678"
    )


def test_senha_com_7_caracteres_e_recusada(form_aluno: dict[str, str]) -> None:
    assert erros_aluno(form_aluno, senha="1234567") == {
        "senha": "A senha precisa ter pelo menos 8 caracteres."
    }


def test_senha_com_128_caracteres_e_aceita(form_aluno: dict[str, str]) -> None:
    assert (
        len(
            auth_service.validar_cadastro_aluno(
                {**form_aluno, "senha": "a" * 128}
            )["senha"]
        )
        == 128
    )


def test_senha_com_129_caracteres_e_recusada(
    form_aluno: dict[str, str],
) -> None:
    assert "senha" in erros_aluno(form_aluno, senha="a" * 129)


# ---------------------------------------------------------------------------
# Cadastro do aluno: entradas inválidas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "email",
    [
        "",
        "gabriel",
        "gabriel@",
        "@escola.br",
        "gabriel@escola",
        "ga briel@escola.br",
    ],
)
def test_email_invalido_e_recusado(
    form_aluno: dict[str, str], email: str
) -> None:
    assert erros_aluno(form_aluno, email=email) == {
        "email": "Informe um e-mail válido."
    }


def test_codigo_da_turma_vazio_pede_o_codigo(
    form_aluno: dict[str, str],
) -> None:
    assert erros_aluno(form_aluno, codigo_turma="") == {
        "codigo_turma": "Informe o código da turma."
    }


@pytest.mark.parametrize("codigo", ["ABC", "ABC-234", "ABCDEFGHI"])
def test_codigo_da_turma_em_formato_errado_e_invalido(
    form_aluno: dict[str, str], codigo: str
) -> None:
    assert erros_aluno(form_aluno, codigo_turma=codigo) == {
        "codigo_turma": "Código de turma inválido."
    }


@pytest.mark.parametrize("consentimento", [None, "", "nao"])
def test_cadastro_sem_consentimento_e_recusado(
    form_aluno: dict[str, str], consentimento: str | None
) -> None:
    form_aluno["consentimento"] = consentimento

    assert erros_aluno(form_aluno) == {
        "consentimento": "Você precisa confirmar a autorização para continuar."
    }


def test_varios_erros_do_cadastro_sao_devolvidos_de_uma_vez(
    form_aluno: dict[str, str],
) -> None:
    erros = erros_aluno(
        form_aluno,
        apelido="",
        email="x",
        senha="1",
        codigo_turma="",
        consentimento="",
    )

    assert set(erros) == {
        "apelido",
        "email",
        "senha",
        "codigo_turma",
        "consentimento",
    }


# ---------------------------------------------------------------------------
# Cadastro do professor (sem código de turma e sem consentimento)
# ---------------------------------------------------------------------------


def test_cadastro_de_professor_valido_devolve_dados_normalizados(
    form_professor: dict[str, str],
) -> None:
    assert auth_service.validar_cadastro_professor(form_professor) == {
        "apelido": "Prof. Ana",
        "email": "ana@escola.br",
        "senha": "senha-segura-123",
    }


def test_cadastro_de_professor_nao_exige_codigo_nem_consentimento(
    form_professor: dict[str, str],
) -> None:
    dados = auth_service.validar_cadastro_professor(form_professor)

    assert "codigo_turma" not in dados


def test_cadastro_de_professor_valida_email(
    form_professor: dict[str, str],
) -> None:
    with pytest.raises(ErroValidacao) as excinfo:
        auth_service.validar_cadastro_professor(
            {**form_professor, "email": "ana"}
        )

    assert excinfo.value.erros == {"email": "Informe um e-mail válido."}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_valido_devolve_email_normalizado_e_senha() -> None:
    dados = auth_service.validar_login(
        {"email": " Ana@Escola.br ", "senha": "qualquer"}
    )

    assert dados == {"email": "ana@escola.br", "senha": "qualquer"}


def test_login_vazio_pede_email_e_senha() -> None:
    with pytest.raises(ErroValidacao) as excinfo:
        auth_service.validar_login({"email": "", "senha": ""})

    assert excinfo.value.erros == {
        "email": "Informe seu e-mail.",
        "senha": "Informe sua senha.",
    }


# ---------------------------------------------------------------------------
# Senha com hash (RNF04)
# ---------------------------------------------------------------------------


def test_hash_da_senha_nao_contem_a_senha() -> None:
    assert "senha-segura-123" not in auth_service.gerar_hash_senha(
        "senha-segura-123"
    )


def test_hash_da_mesma_senha_muda_a_cada_vez() -> None:
    assert auth_service.gerar_hash_senha(
        "abc12345"
    ) != auth_service.gerar_hash_senha("abc12345")


def test_hash_novo_e_argon2id() -> None:
    assert auth_service.gerar_hash_senha("senha-segura-123").startswith(
        "$argon2id$"
    )


def test_senha_certa_com_hash_novo_confere_sem_pedir_rehash() -> None:
    hash_senha = auth_service.gerar_hash_senha("senha-segura-123")

    assert auth_service.conferir_senha(hash_senha, "senha-segura-123") == (
        True,
        None,
    )


def test_senha_certa_com_hash_scrypt_antigo_confere_e_devolve_argon2id() -> (
    None
):
    # Formato das contas criadas antes do Argon2id (o padrão do Werkzeug no deploy).
    hash_antigo = generate_password_hash("senha-segura-123", method="scrypt")

    confere, hash_novo = auth_service.conferir_senha(
        hash_antigo, "senha-segura-123"
    )

    assert confere is True
    assert hash_novo.startswith("$argon2id$")


def test_senha_errada_nao_confere_com_hash_novo() -> None:
    hash_senha = auth_service.gerar_hash_senha("senha-segura-123")

    assert auth_service.conferir_senha(hash_senha, "senha-errada") == (
        False,
        None,
    )


def test_senha_errada_nao_confere_com_hash_scrypt_antigo() -> None:
    hash_antigo = generate_password_hash("senha-segura-123", method="scrypt")

    assert auth_service.conferir_senha(hash_antigo, "senha-errada") == (
        False,
        None,
    )
