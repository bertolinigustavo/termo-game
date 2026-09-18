"""Teste "de fumaça" da interface: a janela monta, desenha e responde ao teclado.

Roda sem abrir janela de verdade (veja conftest.py). Não avalia aparência — para isso, abra
o jogo com `uv run termo`. Cada tecla que o jogo entende tem um teste aqui: se você criar
uma interação nova, crie o teste dela também.
"""

import pygame
import pytest

from termo.gui import (
    ALTURA_JANELA,
    DICA,
    DICA_FIM,
    LARGURA_JANELA,
    MARGEM,
    Tela,
)
from termo.jogo import (
    AVISO_DERROTA,
    MAXIMO_TENTATIVAS,
    TAMANHO_PALAVRA,
    Jogo,
    Situacao,
)
from termo.palavras import carregar_palavras

ALTURA_MAXIMA_DE_TELA_PEQUENA = 700


@pytest.fixture
def tela():
    """Cria a janela (sem tela) com uma palavra conhecida e desliga o pygame no fim."""
    tela = Tela(Jogo("TERMO"))
    yield tela
    pygame.quit()


def apertar(tela: Tela, tecla: int, letra: str = "") -> None:
    """Simula apertar uma tecla do teclado."""
    tela.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=tecla, unicode=letra))


def digitar(tela: Tela, palavra: str) -> None:
    """Simula digitar uma palavra inteira, letra por letra."""
    for letra in palavra:
        apertar(tela, ord(letra.lower()), letra)


def clicar(tela: Tela, ponto: tuple[int, int], botao: int = 1) -> None:
    """Simula um clique do mouse num ponto da janela (botão 1 é o esquerdo)."""
    tela.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=ponto, button=botao))


# ----- A janela -----


def test_a_janela_tem_o_tamanho_esperado(tela):
    """A janela é título + grade + aviso + teclado, nada mais."""
    assert tela.janela.get_size() == (LARGURA_JANELA, ALTURA_JANELA)


def test_a_janela_cabe_em_notebook_pequeno(tela):
    """A janela precisa caber em tela de 1366x768 com a barra de tarefas.

    Por quê: numa janela mais alta que isso, o teclado e o aviso ficam embaixo da barra de
    tarefas do Windows e a pessoa joga sem ver o que o jogo está dizendo.
    """
    assert ALTURA_JANELA <= ALTURA_MAXIMA_DE_TELA_PEQUENA


def test_a_grade_cabe_dentro_da_janela(tela):
    """O último quadradinho da grade não pode passar da borda da janela."""
    ultima = tela.retangulo_da_casa(MAXIMO_TENTATIVAS - 1, TAMANHO_PALAVRA - 1)
    assert ultima.right <= LARGURA_JANELA
    assert ultima.bottom <= ALTURA_JANELA


def test_todo_aviso_cabe_na_largura_da_janela(tela):
    """Nenhum recado do jogo pode passar da borda da janela.

    Por quê: texto mais largo que a janela aparece cortado nas duas pontas, e foi o que
    aconteceu com a primeira versão da dica. O caso mais comprido é a derrota, que junta a
    palavra secreta com a instrução de recomeçar — por isso o teste usa a palavra mais larga
    da lista inteira, e não uma escolhida a dedo.
    """
    mais_larga = max(carregar_palavras(), key=lambda palavra: tela.fonte_aviso.size(palavra)[0])
    derrota = f"{AVISO_DERROTA.format(palavra=mais_larga)} · {DICA_FIM}"
    for texto in (DICA, derrota):
        assert tela.fonte_aviso.size(texto)[0] <= LARGURA_JANELA - 2 * MARGEM


def test_a_fonte_desenha_letra_acentuada(tela):
    """A fonte usada precisa ter Á, Ç e Ã.

    Por quê: o jogo revela o acento nas letras certas. Numa fonte sem esses desenhos, LIÇÃO
    apareceria com quadradinhos vazios no lugar das letras — e ninguém entenderia a palavra.
    """
    assert None not in tela.fonte_letra.metrics("ÁÂÃÀÉÊÍÓÔÕÚÇ")


# ----- Desenhar -----


def test_desenha_a_grade_vazia_sem_quebrar(tela):
    """Desenhar o primeiro quadro não pode falhar — senão o jogo abre e fecha na hora."""
    tela.desenhar()


def test_desenha_partida_em_andamento_sem_quebrar(tela):
    """Com uma tentativa feita e outra sendo digitada, a grade desenha os três tipos de casa."""
    digitar(tela, "CASAL")
    apertar(tela, pygame.K_RETURN)
    digitar(tela, "PRE")
    tela.desenhar()


def test_desenha_vitoria_e_derrota_sem_quebrar(tela):
    """Os dois fins de jogo desenham sem erro, inclusive o aviso mais comprido (a derrota)."""
    digitar(tela, "TERMO")
    apertar(tela, pygame.K_RETURN)
    assert tela.jogo.situacao is Situacao.VITORIA
    tela.desenhar()

    perdida = Tela(Jogo("TERMO"))
    for _ in range(MAXIMO_TENTATIVAS):
        digitar(perdida, "CASAL")
        apertar(perdida, pygame.K_RETURN)
    assert perdida.jogo.situacao is Situacao.DERROTA
    perdida.desenhar()


# ----- Teclado -----


def test_digitar_uma_letra_aparece_no_chute(tela):
    """Apertar uma letra monta o chute — é o gesto principal do jogo."""
    digitar(tela, "CA")
    assert tela.jogo.digitando == ["C", "A", "", "", ""]


def test_enter_envia_o_chute(tela):
    """Enter manda o chute e a linha vira histórico."""
    digitar(tela, "CASAL")
    apertar(tela, pygame.K_RETURN)
    assert len(tela.jogo.tentativas) == 1


def test_backspace_apaga_a_ultima_letra(tela):
    """Backspace corrige quem digitou errado."""
    digitar(tela, "CASA")
    apertar(tela, pygame.K_BACKSPACE)
    assert tela.jogo.digitando == ["C", "A", "S", "", ""]


def test_tecla_r_durante_a_partida_e_uma_letra_como_outra_qualquer(tela):
    """Durante o jogo, R escreve R.

    Por quê: se R reiniciasse a qualquer momento, ninguém conseguiria chutar TERRA nem
    CARRO — e a pessoa perderia a partida inteira sem entender o que aconteceu.
    """
    apertar(tela, pygame.K_r, "r")
    assert tela.jogo.digitando == ["R", "", "", "", ""]
    assert tela.jogo.tentativas == []


def test_tecla_r_depois_do_fim_comeca_outra_partida(tela):
    """Acabou a partida, R começa outra — sem precisar fechar e abrir o jogo."""
    digitar(tela, "TERMO")
    apertar(tela, pygame.K_RETURN)
    apertar(tela, pygame.K_r, "r")
    assert tela.jogo.situacao is Situacao.JOGANDO
    assert tela.jogo.tentativas == []


def test_setas_andam_com_a_casa_selecionada(tela):
    """As setas escolhem a casa sem tirar a mão do teclado.

    Por quê: é a alternativa ao mouse. Sem ela, quem joga só de teclado não alcança a
    escolha da casa.
    """
    apertar(tela, pygame.K_RIGHT)
    apertar(tela, pygame.K_RIGHT)
    digitar(tela, "A")
    assert tela.jogo.digitando == ["", "", "A", "", ""]


def test_seta_nao_escreve_letra_nenhuma(tela):
    """Apertar as setas não acrescenta caractere ao chute.

    Por quê: no fim do `tratar_evento`, qualquer tecla não mapeada vira letra. Em algumas
    plataformas a seta chega com um caractere junto — e ele apareceria na grade.
    """
    apertar(tela, pygame.K_LEFT, "")
    apertar(tela, pygame.K_RIGHT, "")
    assert tela.jogo.digitando == ["", "", "", "", ""]


# ----- Mouse -----


def test_clique_numa_casa_escolhe_onde_a_letra_vai_entrar(tela):
    """Clicar num quadradinho da linha atual faz a próxima letra cair ali.

    Por quê: é o gesto que esta feature criou. Sem ele, a letra apareceria noutro lugar e a
    pessoa acharia que o jogo ignorou o mouse.
    """
    clicar(tela, tela.retangulo_da_casa(0, 2).center)
    digitar(tela, "A")
    assert tela.jogo.digitando == ["", "", "A", "", ""]


def test_clique_numa_linha_que_nao_e_a_atual_e_ignorado(tela):
    """Clicar numa linha que não está sendo digitada não mexe na seleção.

    Por quê: as outras linhas são histórico ou futuro. Chute já enviado não se edita, e a
    coluna clicada lá não tem relação com a linha de agora.
    """
    clicar(tela, tela.retangulo_da_casa(3, 4).center)
    assert tela.jogo.cursor == 0


def test_clique_fora_da_grade_nao_muda_nada(tela):
    """Clicar no título, no aviso ou no teclado desenhado não mexe na seleção."""
    clicar(tela, (MARGEM, MARGEM))
    assert tela.jogo.cursor == 0


def test_rolar_a_roda_do_mouse_nao_mexe_na_selecao(tela):
    """Só o botão esquerdo escolhe a casa.

    Por quê: a roda do mouse chega como o mesmo tipo de evento (botões 4 e 5). Sem filtrar o
    botão, rolar a roda em cima da grade mudaria a casa escolhida sozinho.
    """
    clicar(tela, tela.retangulo_da_casa(0, 3).center, botao=4)
    assert tela.jogo.cursor == 0


def test_clique_depois_do_fim_da_partida_e_ignorado(tela):
    """Acabada a partida, clicar na grade não seleciona nada.

    Por quê: a "linha atual" passa a ser uma linha que não existe na grade, e o retângulo
    calculado para ela cai em cima da faixa do aviso — um clique ali acertaria uma casa
    fantasma.
    """
    digitar(tela, "TERMO")
    apertar(tela, pygame.K_RETURN)
    assert tela.coluna_clicada(tela.retangulo_da_casa(0, 2).center) is None


# ----- A casa selecionada -----


def test_nao_ha_casa_destacada_com_a_linha_cheia(tela):
    """Digitadas as cinco letras e antes do Enter, nenhuma casa fica destacada.

    Por quê: nesse instante a seleção está fora da linha, e é o estado em que toda partida
    passa. Se o desenho procurasse a casa mesmo assim, o jogo fecharia sozinho no meio do jogo.
    """
    digitar(tela, "CASAL")
    assert tela.casa_selecionada() is None
    tela.desenhar()


def test_nao_ha_casa_destacada_depois_do_fim(tela):
    """Acabada a partida, nenhum quadradinho fica destacado.

    Por quê: um destaque numa linha vazia depois da vitória sugere que ainda dá para jogar, e
    a pessoa fica digitando sem entender por que nada acontece.
    """
    digitar(tela, "TERMO")
    apertar(tela, pygame.K_RETURN)
    assert tela.casa_selecionada() is None
    tela.desenhar()


def test_esc_encerra_o_jogo(tela):
    """Esc para o loop principal (o jogo fecha no próximo quadro)."""
    assert tela.rodando
    apertar(tela, pygame.K_ESCAPE)
    assert not tela.rodando


def test_fechar_a_janela_encerra_o_jogo(tela):
    """O X da janela encerra o jogo — sem isso, a janela ficaria presa aberta."""
    tela.tratar_evento(pygame.event.Event(pygame.QUIT))
    assert not tela.rodando
