"""Regras do jogo do Termo — lógica pura, sem nenhuma dependência de interface.

Este módulo NÃO importa pygame. Ele só sabe responder perguntas como "essa letra está no
lugar certo?", "a partida acabou?" e "o que já foi digitado?". Toda a parte visual fica em
`gui.py`, que consulta este módulo e desenha a resposta.
"""

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from termo.palavras import canonica, sem_acento, sortear_palavra

TAMANHO_PALAVRA = 5
MAXIMO_TENTATIVAS = 6

CASA_VAZIA = ""
"""O que fica numa casa da linha atual enquanto ninguém digitou nela."""

CURSOR_FIM_DA_LINHA = TAMANHO_PALAVRA
"""Cursor "depois da última casa": a linha está cheia e nenhuma casa está selecionada.

É o mesmo que acontece num campo de texto quando o traço piscando vai parar depois da
última letra: não há mais onde escrever, só resta apagar ou mandar.
"""

# Textos que a tela mostra. Ficam aqui, e não na `gui.py`, porque quem sabe que o chute está
# incompleto ou que a partida terminou é o jogo — a tela só desenha o que ele disser.
AVISO_FALTAM_LETRAS = "Faltam letras"
AVISO_VITORIA = "Acertou!"
AVISO_DERROTA = "A palavra era {palavra}"


class Marca(Enum):
    """Como uma letra do chute foi avaliada — é o que define a cor do quadradinho."""

    CERTA = "certa"
    """A letra existe na palavra e está na posição certa (verde)."""

    DESLOCADA = "deslocada"
    """A letra existe na palavra, mas em outra posição (amarelo)."""

    AUSENTE = "ausente"
    """A letra não existe na palavra — ou já foi contada em outra posição (cinza)."""


class Situacao(Enum):
    """Em que pé está a partida."""

    JOGANDO = "jogando"
    VITORIA = "vitoria"
    DERROTA = "derrota"


@dataclass(frozen=True)
class Letra:
    """Uma letra já avaliada, do jeito que a tela precisa desenhar."""

    letra: str
    """O caractere que aparece na tela — com acento quando o jogo já pode revelá-lo."""

    marca: Marca
    """Certa, deslocada ou ausente."""


def avaliar(chute: str, secreta: str) -> list[Letra]:
    """Compara um chute com a palavra secreta e devolve a marca de cada letra.

    A comparação é feita sem acento, mas a letra acentuada da palavra secreta é revelada
    nas posições certas — é o que o Termo original faz: você digita `ACAO` e vê `AÇÃO`.

    A conta é feita em DOIS passos, e a ordem importa: primeiro as letras na posição certa,
    e só depois as deslocadas, consumindo o que sobrou. Ver a docstring dos testes de letra
    repetida para o que acontece quando se tenta fazer isso num passo só.
    """
    chute_simples = sem_acento(chute)
    secreta_simples = sem_acento(secreta)
    if len(chute_simples) != len(secreta_simples):
        raise ValueError(f"O chute '{chute}' e a palavra '{secreta}' precisam ter o mesmo tamanho.")

    marcas = [Marca.AUSENTE] * len(chute_simples)
    exibicao = list(chute_simples)
    # Quantas vezes cada letra da secreta ainda está disponível para virar amarelo.
    sobrando: Counter[str] = Counter()

    # Passo 1 — as que estão no lugar certo. O resto da palavra secreta fica no contador.
    for posicao, letra in enumerate(chute_simples):
        if letra == secreta_simples[posicao]:
            marcas[posicao] = Marca.CERTA
            exibicao[posicao] = secreta[posicao]
        else:
            sobrando[secreta_simples[posicao]] += 1

    # Passo 2 — as deslocadas, uma por ocorrência que sobrou. Sem isso, chutar duas letras
    # iguais numa palavra que só tem uma acenderia os dois quadradinhos de amarelo.
    for posicao, letra in enumerate(chute_simples):
        if marcas[posicao] is Marca.CERTA:
            continue
        if sobrando[letra] > 0:
            marcas[posicao] = Marca.DESLOCADA
            sobrando[letra] -= 1

    return [Letra(exibicao[posicao], marcas[posicao]) for posicao in range(len(chute_simples))]


class Jogo:
    """Uma partida do Termo: a palavra secreta, as tentativas feitas e o que está sendo digitado."""

    def __init__(self, secreta: str | None = None) -> None:
        """Começa uma partida. Sem argumento, sorteia a palavra; com argumento, usa a que você deu.

        Passar a palavra é o que permite os testes serem previsíveis — e é assim que a tela
        de "modo treino" poderia funcionar um dia.
        """
        self.secreta = ""
        self.tentativas: list[list[Letra]] = []
        self.digitando: list[str] = [CASA_VAZIA] * TAMANHO_PALAVRA
        self.cursor = 0
        self.situacao = Situacao.JOGANDO
        self.aviso = ""
        self._comecar(secreta)

    # ----- Estado da partida -----

    @property
    def acabou(self) -> bool:
        """Diz se a partida terminou, por vitória ou por derrota."""
        return self.situacao is not Situacao.JOGANDO

    @property
    def tentativas_restantes(self) -> int:
        """Quantas tentativas ainda cabem."""
        return MAXIMO_TENTATIVAS - len(self.tentativas)

    @property
    def linha_atual(self) -> int:
        """Qual linha da grade está sendo digitada agora (contando do 0).

        Fica aqui, e não na tela, porque "a linha atual é a de número igual à quantidade de
        tentativas já feitas" é regra do jogo, não geometria.
        """
        return len(self.tentativas)

    def letras_usadas(self) -> dict[str, Marca]:
        """A melhor marca já obtida por cada letra, para colorir o teclado da tela.

        "Melhor" é certa > deslocada > ausente: uma letra que já apareceu em verde não pode
        voltar a amarelo só porque num chute posterior ela caiu no lugar errado.
        """
        prioridade = {Marca.AUSENTE: 0, Marca.DESLOCADA: 1, Marca.CERTA: 2}
        melhor: dict[str, Marca] = {}
        for tentativa in self.tentativas:
            for letra in tentativa:
                simples = sem_acento(letra.letra)
                atual = melhor.get(simples)
                if atual is None or prioridade[letra.marca] > prioridade[atual]:
                    melhor[simples] = letra.marca
        return melhor

    # ----- O que a pessoa faz -----

    def digitar(self, tecla: str) -> None:
        """Escreve a letra na casa selecionada e passa a seleção para a próxima casa vazia.

        A letra TROCA a que estiver na casa: é isso que permite corrigir o meio da palavra
        sem apagar o que veio depois. Tecla que não é letra e linha cheia são ignoradas.
        """
        if self.acabou or self.cursor == CURSOR_FIM_DA_LINHA:
            return
        letra = sem_acento(tecla)
        if len(letra) != 1 or not letra.isalpha():
            return
        self.digitando[self.cursor] = letra
        self.cursor = self._proxima_casa_vazia(self.cursor + 1)
        self.aviso = ""

    def apagar(self) -> None:
        """Apaga a letra da casa selecionada; se ela já estiver vazia, apaga a de trás.

        É o que faz o Backspace continuar parecendo o de sempre: depois de digitar as cinco
        letras, apertar Backspace seguidamente desfaz uma letra por vez, da direita para a
        esquerda. E, com uma casa escolhida a dedo, ele limpa só aquela casa.
        """
        if self.acabou:
            return
        if self.cursor == CURSOR_FIM_DA_LINHA:
            self.cursor = TAMANHO_PALAVRA - 1
        elif self.digitando[self.cursor] == CASA_VAZIA and self.cursor > 0:
            self.cursor -= 1
        self.digitando[self.cursor] = CASA_VAZIA
        self.aviso = ""

    def mover_cursor(self, passo: int) -> None:
        """Anda com a casa selecionada: `-1` para a esquerda, `+1` para a direita.

        Nas pontas da linha a seleção para, não dá a volta: a grade tem começo e fim à vista,
        e um cursor que salta do fim para o começo parece defeito. Recebe `-1`/`+1` em vez da
        tecla do pygame porque este módulo não conhece pygame.
        """
        if self.acabou:
            return
        self.cursor = max(0, min(TAMANHO_PALAVRA - 1, self.cursor + passo))

    def selecionar(self, posicao: int) -> None:
        """Escolhe em qual casa da linha atual a próxima letra vai entrar — é o clique do mouse.

        Posição fora da linha é ignorada em silêncio: quem chama é a tela, que pergunta a
        partir de um clique que pode ter caído em qualquer canto da janela. E um número
        negativo, em Python, escolheria a casa do fim sem reclamar.
        """
        if self.acabou or not 0 <= posicao < TAMANHO_PALAVRA:
            return
        self.cursor = posicao

    def enviar(self) -> bool:
        """Manda o chute atual. Devolve se ele foi aceito.

        Chute com casa vazia não é aceito e NÃO gasta tentativa: a pessoa só apertou Enter cedo
        demais, e perder uma das seis chances por isso seria punição sem motivo.
        """
        if self.acabou:
            return False
        if CASA_VAZIA in self.digitando:
            self.aviso = AVISO_FALTAM_LETRAS
            return False

        tentativa = avaliar("".join(self.digitando), self.secreta)
        self.tentativas.append(tentativa)
        self._limpar_linha()

        if all(letra.marca is Marca.CERTA for letra in tentativa):
            self.situacao = Situacao.VITORIA
            self.aviso = AVISO_VITORIA
        elif len(self.tentativas) >= MAXIMO_TENTATIVAS:
            self.situacao = Situacao.DERROTA
            self.aviso = AVISO_DERROTA.format(palavra=self.secreta)
        else:
            self.aviso = ""
        return True

    def reiniciar(self) -> None:
        """Começa outra partida, com uma palavra nova sorteada."""
        self._comecar(None)

    # ----- Detalhe interno -----

    def _proxima_casa_vazia(self, a_partir_de: int) -> int:
        """A primeira casa vazia a partir da posição dada, dando a volta na linha.

        Dar a volta é o que faz a seleção achar o buraco que ficou para trás: com `C_SA_`, ao
        preencher a última casa a seleção precisa voltar para a casa 1 — senão o jogo diria
        "faltam letras" sem mostrar onde falta. Devolve `CURSOR_FIM_DA_LINHA` quando não
        sobrou nenhuma casa vazia.
        """
        for passo in range(TAMANHO_PALAVRA):
            posicao = (a_partir_de + passo) % TAMANHO_PALAVRA
            if self.digitando[posicao] == CASA_VAZIA:
                return posicao
        return CURSOR_FIM_DA_LINHA

    def _limpar_linha(self) -> None:
        """Deixa a linha que está sendo digitada em branco, com a primeira casa selecionada."""
        self.digitando = [CASA_VAZIA] * TAMANHO_PALAVRA
        self.cursor = 0

    def _comecar(self, secreta: str | None) -> None:
        """Zera o estado e define a palavra secreta desta partida."""
        # `canonica` cola cada acento na sua letra antes de contar: sem isso, uma palavra
        # escrita com a cedilha solta teria 7 caracteres e a grade mostraria o acento sozinho.
        palavra = canonica(secreta or sortear_palavra())
        if len(palavra) != TAMANHO_PALAVRA or len(sem_acento(palavra)) != TAMANHO_PALAVRA:
            raise ValueError(
                f"A palavra secreta precisa ter {TAMANHO_PALAVRA} letras, e '{palavra}' não tem."
            )
        self.secreta = palavra
        self.tentativas = []
        self._limpar_linha()
        self.situacao = Situacao.JOGANDO
        self.aviso = ""
