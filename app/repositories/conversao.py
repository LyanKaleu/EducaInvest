"""Conversão das linhas do SQLite para tipos simples, compartilhada pelos repositórios."""
import sqlite3


def linha_para_dict(linha: sqlite3.Row | None) -> dict | None:
    """Converte uma linha do banco em dict.

    Args:
        linha: resultado de `fetchone()`, ou None quando nada foi encontrado.

    Returns:
        dict | None: as colunas da linha, ou None se `linha` for None.
    """
    return dict(linha) if linha is not None else None
