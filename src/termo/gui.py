"""Interface gráfica do jogo do Termo, feita com pygame.

Este módulo só DESENHA e trata as teclas. Quem sabe as regras é o `Jogo`, em `jogo.py`:
a tela pergunta ("que letras já foram?", "a partida acabou?") e pinta a resposta.
Para mudar a aparência do jogo (cores, tamanho, textos), comece pelas constantes logo abaixo.
"""

import pygame

from termo.jogo import CURSOR_FIM_DA_LINHA, MAXIMO_TENTATIVAS, TAMANHO_PALAVRA, Jogo, Marca

# --- Tamanhos (em pixels) ---
LADO_CASA = 56  # lado de cada quadradinho da grade
ESPACO_CASA = 6  # respiro entre dois quadradinhos
MARGEM = 20  # respiro nas bordas da janela
ALTURA_TITULO = 52  # faixa do nome do jogo, no topo
ALTURA_AVISO = 34  # faixa da mensagem, entre a grade e o teclado
LARGURA_TECLA = 36
ALTURA_TECLA = 46
ESPACO_TECLA = 5
FPS = 30  # quantos quadros por segundo o jogo desenha

# --- Entrada ---
# Só o botão esquerdo escolhe a casa: a roda do mouse também chega como MOUSEBUTTONDOWN
# (botões 4 e 5), e sem este filtro rolar a roda em cima da grade mudaria a casa sozinho.
BOTAO_ESQUERDO = 1

# --- Cores (vermelho, verde, azul, de 0 a 255) ---
FUNDO = (18, 18, 19)
BORDA_VAZIA = (58, 58, 60)
BORDA_DIGITANDO = (104, 106, 110)
BORDA_SELECIONADA = (245, 245, 245)  # a casa onde a próxima letra vai entrar
LARGURA_BORDA_SELECIONADA = 3  # mais grossa que as outras, para saltar aos olhos
COR_CERTA = (59, 138, 122)
COR_DESLOCADA = (200, 165, 90)
COR_AUSENTE = (58, 51, 53)
COR_TECLA_LIVRE = (86, 88, 92)
TEXTO = (245, 245, 245)
TEXTO_APAGADO = (150, 152, 155)

# --- Textos ---
TITULO_JANELA = "Termo — descubra a palavra"
DICA = "Digite · clique ou setas escolhem a casa · Esc sai"
DICA_FIM = "R joga de novo · Esc sai"

# O teclado da tela é só um resumo colorido do que já se sabe: ele mostra as letras,
# não recebe clique. Deixar clicável é uma das ideias do IDEIAS.md. (Quem recebe clique é a
# GRADE, para escolher em que casa a letra entra — ver `tratar_clique`.)
FILEIRAS_DO_TECLADO = ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")

# --- Geometria da janela (calculada a partir do que está acima) ---
LARGURA_GRADE = TAMANHO_PALAVRA * LADO_CASA + (TAMANHO_PALAVRA - 1) * ESPACO_CASA
ALTURA_GRADE = MAXIMO_TENTATIVAS * LADO_CASA + (MAXIMO_TENTATIVAS - 1) * ESPACO_CASA
LARGURA_TECLADO = 10 * LARGURA_TECLA + 9 * ESPACO_TECLA
ALTURA_TECLADO = 3 * ALTURA_TECLA + 2 * ESPACO_TECLA

LARGURA_JANELA = max(LARGURA_GRADE, LARGURA_TECLADO) + 2 * MARGEM
ALTURA_JANELA = MARGEM + ALTURA_TITULO + ALTURA_GRADE + ALTURA_AVISO + ALTURA_TECLADO + MARGEM

TOPO_GRADE = MARGEM + ALTURA_TITULO
TOPO_AVISO = TOPO_GRADE + ALTURA_GRADE
TOPO_TECLADO = TOPO_AVISO + ALTURA_AVISO


def cor_da_marca(marca: Marca) -> tuple[int, int, int]:
    """A cor de fundo de um quadradinho conforme o jogo avaliou aquela letra."""
    if marca is Marca.CERTA:
        return COR_CERTA
    if marca is Marca.DESLOCADA:
        return COR_DESLOCADA
    return COR_AUSENTE


class Tela:
    """A janela do jogo: desenha a grade, o aviso e o teclado, e repassa as teclas ao `Jogo`."""

    def __init__(self, jogo: Jogo | None = None) -> None:
        """Abre a janela. Receber um `Jogo` pronto é o que deixa os testes previsíveis."""
        pygame.init()
        self.jogo = jogo or Jogo()
        self.janela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
        pygame.display.set_caption(TITULO_JANELA)
        self.relogio = pygame.time.Clock()
        self.rodando = True

        # A fonte embutida do pygame já tem os acentos do português — conferido em
        # tests/test_gui_smoke.py, porque uma fonte sem acento desenharia quadradinhos vazios.
        self.fonte_titulo = pygame.font.Font(None, 40)
        self.fonte_letra = pygame.font.Font(None, 48)
        self.fonte_aviso = pygame.font.Font(None, 24)
        self.fonte_tecla = pygame.font.Font(None, 26)

    # ----- Ciclo de vida -----

    def rodar(self) -> None:
        """Loop principal: trata as teclas, desenha um quadro e repete, FPS vezes por segundo."""
        while self.rodando:
            for evento in pygame.event.get():
                self.tratar_evento(evento)
            self.desenhar()
            pygame.display.flip()
            self.relogio.tick(FPS)
        pygame.quit()

    # ----- Entrada (teclado e mouse) -----

    def tratar_evento(self, evento: pygame.event.Event) -> None:
        """Traduz um evento do pygame numa ação do jogo."""
        if evento.type == pygame.QUIT:
            self.rodando = False
            return
        if evento.type == pygame.MOUSEBUTTONDOWN:
            self.tratar_clique(evento)
            return
        if evento.type != pygame.KEYDOWN:
            return

        if evento.key == pygame.K_ESCAPE:
            self.rodando = False
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.jogo.enviar()
        elif evento.key == pygame.K_BACKSPACE:
            self.jogo.apagar()
        elif evento.key == pygame.K_LEFT:
            # As setas vêm antes do `else` de propósito: lá embaixo qualquer tecla vira letra,
            # e em algumas plataformas o `unicode` da seta não é vazio.
            self.jogo.mover_cursor(-1)
        elif evento.key == pygame.K_RIGHT:
            self.jogo.mover_cursor(1)
        elif evento.key == pygame.K_r and self.jogo.acabou:
            # R só reinicia depois do fim. Durante a partida, R é uma letra como outra
            # qualquer — senão ninguém conseguiria chutar uma palavra com R.
            self.jogo.reiniciar()
        else:
            self.jogo.digitar(evento.unicode)

    def tratar_clique(self, evento: pygame.event.Event) -> None:
        """Clicar num quadradinho da linha atual escolhe onde a próxima letra vai entrar."""
        if evento.button != BOTAO_ESQUERDO:
            return
        coluna = self.coluna_clicada(evento.pos)
        if coluna is not None:
            self.jogo.selecionar(coluna)

    # ----- Geometria -----

    def coluna_clicada(self, ponto: tuple[int, int]) -> int | None:
        """Em qual casa da linha que está sendo digitada o clique caiu, ou `None` fora dela.

        A busca para quando a partida acaba: aí a "linha atual" é a sétima, que não existe na
        grade, e o retângulo calculado para ela cairia em cima da faixa do aviso.
        """
        if self.jogo.acabou:
            return None
        for coluna in range(TAMANHO_PALAVRA):
            if self.retangulo_da_casa(self.jogo.linha_atual, coluna).collidepoint(ponto):
                return coluna
        return None

    def retangulo_da_casa(self, linha: int, coluna: int) -> pygame.Rect:
        """Onde fica, na janela, o quadradinho da linha e coluna pedidas (contando do 0)."""
        borda_esquerda = (LARGURA_JANELA - LARGURA_GRADE) // 2
        return pygame.Rect(
            borda_esquerda + coluna * (LADO_CASA + ESPACO_CASA),
            TOPO_GRADE + linha * (LADO_CASA + ESPACO_CASA),
            LADO_CASA,
            LADO_CASA,
        )

    # ----- Desenho -----

    def desenhar(self) -> None:
        """Desenha um quadro inteiro: título, grade, aviso e teclado."""
        self.janela.fill(FUNDO)
        self.desenhar_titulo()
        self.desenhar_grade()
        self.desenhar_aviso()
        self.desenhar_teclado()

    def desenhar_titulo(self) -> None:
        """Escreve o nome do jogo no topo da janela."""
        area = pygame.Rect(0, MARGEM, LARGURA_JANELA, ALTURA_TITULO)
        self.escrever("TERMO", self.fonte_titulo, TEXTO, area)

    def desenhar_grade(self) -> None:
        """Desenha as seis linhas de cinco quadradinhos, cada uma no seu estado."""
        for linha in range(MAXIMO_TENTATIVAS):
            for coluna in range(TAMANHO_PALAVRA):
                self.desenhar_casa(linha, coluna)

    def casa_selecionada(self) -> int | None:
        """Qual coluna está destacada agora, ou `None` quando não há nenhuma.

        Não há destaque com a partida encerrada (a grade congela) nem com a linha cheia,
        esperando o Enter — nesse instante a seleção está fora da linha.
        """
        if self.jogo.acabou or self.jogo.cursor == CURSOR_FIM_DA_LINHA:
            return None
        return self.jogo.cursor

    def desenhar_casa(self, linha: int, coluna: int) -> None:
        """Desenha um quadradinho: já avaliado (colorido), sendo digitado, ou ainda vazio."""
        area = self.retangulo_da_casa(linha, coluna)
        tentativas = self.jogo.tentativas

        if linha < len(tentativas):
            letra = tentativas[linha][coluna]
            pygame.draw.rect(self.janela, cor_da_marca(letra.marca), area, border_radius=4)
            self.escrever(letra.letra, self.fonte_letra, TEXTO, area)
            return

        na_linha_atual = linha == self.jogo.linha_atual
        letra = self.jogo.digitando[coluna] if na_linha_atual else ""
        # A casa escolhida é destacada mesmo vazia: com a posição livre, ela é a única coisa
        # na tela que responde "para onde vai a letra que eu digitar agora?".
        if na_linha_atual and coluna == self.casa_selecionada():
            cor_borda, grossura = BORDA_SELECIONADA, LARGURA_BORDA_SELECIONADA
        else:
            cor_borda, grossura = (BORDA_DIGITANDO if letra else BORDA_VAZIA), 2
        pygame.draw.rect(self.janela, cor_borda, area, width=grossura, border_radius=4)
        if letra:
            self.escrever(letra, self.fonte_letra, TEXTO, area)

    def desenhar_aviso(self) -> None:
        """Mostra o recado do jogo ou, quando não há recado, a dica de como jogar."""
        if self.jogo.acabou:
            texto = f"{self.jogo.aviso} · {DICA_FIM}"
        else:
            texto = self.jogo.aviso or DICA
        cor = TEXTO if self.jogo.aviso else TEXTO_APAGADO
        area = pygame.Rect(0, TOPO_AVISO, LARGURA_JANELA, ALTURA_AVISO)
        self.escrever(texto, self.fonte_aviso, cor, area)

    def desenhar_teclado(self) -> None:
        """Desenha o teclado com a melhor cor já obtida por cada letra."""
        usadas = self.jogo.letras_usadas()
        for numero, fileira in enumerate(FILEIRAS_DO_TECLADO):
            largura = len(fileira) * LARGURA_TECLA + (len(fileira) - 1) * ESPACO_TECLA
            esquerda = (LARGURA_JANELA - largura) // 2
            topo = TOPO_TECLADO + numero * (ALTURA_TECLA + ESPACO_TECLA)
            for posicao, letra in enumerate(fileira):
                area = pygame.Rect(
                    esquerda + posicao * (LARGURA_TECLA + ESPACO_TECLA),
                    topo,
                    LARGURA_TECLA,
                    ALTURA_TECLA,
                )
                marca = usadas.get(letra)
                cor = cor_da_marca(marca) if marca else COR_TECLA_LIVRE
                pygame.draw.rect(self.janela, cor, area, border_radius=4)
                self.escrever(letra, self.fonte_tecla, TEXTO, area)

    def escrever(
        self, texto: str, fonte: pygame.font.Font, cor: tuple[int, int, int], area: pygame.Rect
    ) -> None:
        """Escreve um texto centralizado dentro de uma área da janela."""
        superficie = fonte.render(texto, True, cor)
        self.janela.blit(superficie, superficie.get_rect(center=area.center))
