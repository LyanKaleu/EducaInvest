"""Limite de tentativas: bloqueia uma chave (o e-mail do login) depois de muitas tentativas seguidas."""
import threading
import time


class LimiteDeTentativas:
    """Conta tentativas por chave numa janela que começa na primeira tentativa.

    A tentativa conta ANTES de a senha ser conferida (`tentar`) e o sucesso
    zera a contagem (`limpar`). Assim, chutes simultâneos não passam todos
    pela conferência antes de qualquer falha ser registrada.

    Fica em memória: vale por processo e zera quando o servidor reinicia. Basta
    para o MVP (um processo), mas não para vários workers.
    """

    def __init__(self, maximo: int, janela_segundos: int, relogio=time.monotonic,
                 max_chaves: int = 10_000):
        self.maximo = maximo
        self.janela_segundos = janela_segundos
        self.relogio = relogio
        self.max_chaves = max_chaves
        self._tentativas: dict[str, tuple[float, int]] = {}  # chave -> (início da janela, tentativas)
        self._trava = threading.Lock()

    def __len__(self) -> int:
        """Quantas chaves estão sendo contadas agora."""
        return len(self._tentativas)

    def _vencida(self, janela: tuple[float, int], agora: float) -> bool:
        return agora - janela[0] >= self.janela_segundos

    def tentar(self, chave) -> bool:
        """Conta uma tentativa. False se a chave já esgotou as tentativas da janela."""
        with self._trava:
            agora = self.relogio()
            if len(self._tentativas) >= self.max_chaves:
                # Muitas chaves (ex.: script com e-mails aleatórios): descarta as vencidas.
                self._tentativas = {c: j for c, j in self._tentativas.items()
                                    if not self._vencida(j, agora)}
            janela = self._tentativas.get(chave)
            if janela is None or self._vencida(janela, agora):
                janela = (agora, 0)  # janela nova: as tentativas antigas não contam mais
            if janela[1] >= self.maximo:
                return False
            self._tentativas[chave] = (janela[0], janela[1] + 1)
            return True

    def limpar(self, chave) -> None:
        with self._trava:
            self._tentativas.pop(chave, None)
