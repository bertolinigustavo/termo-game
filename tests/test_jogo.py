"""Testes das regras do jogo — rodam sem pygame e sem abrir janela.

Cada teste guarda o porquê de uma regra existir. Quando um deles quebrar, leia a docstring
antes de mexer no código: ela diz o que a pessoa que joga perderia.
"""

import ast
import unicodedata
from pathlib import Path

import pytest

from termo import jogo as modulo_jogo
from termo import palavras as modulo_palavras
from termo.jogo import (
    AVISO_FALTAM_LETRAS,
    CURSOR_FIM_DA_LINHA,
    MAXIMO_TENTATIVAS,
    TAMANHO_PALAVRA,
    Jogo,
    Marca,
    Situacao,
    avaliar,
)

CERTA = Marca.CERTA
DESLOCADA = Marca.DESLOCADA
AUSENTE = Marca.AUSENTE


def marcas(chute: str, secreta: str) -> list[Marca]:
    """Atalho: só as cores de um chute, sem as letras, para o teste caber numa linha."""
    return [letra.marca for letra in avaliar(chute, secreta)]


def exibicao(chute: str, secreta: str) -> str:
    """Atalho: só o texto que apareceria na tela depois de avaliar o chute."""
    return "".join(letra.letra for letra in avaliar(chute, secreta))


def chute_visivel(jogo: Jogo) -> str:
    """Atalho: a linha que está sendo digitada como texto, com `_` onde a casa está vazia."""
    return "".join(letra or "_" for letra in jogo.digitando)


def digitar_tudo(jogo: Jogo, teclas: str) -> None:
    """Atalho: digita as teclas uma a uma, como a pessoa faria."""
    for tecla in teclas:
        jogo.digitar(tecla)


def modulos_importados_por(modulo) -> set[str]:
    """Lê o código-fonte de um módulo e devolve os nomes que ele importa."""
    importados: set[str] = set()
    codigo = Path(modulo.__file__).read_text(encoding="utf-8")
    for no in ast.walk(ast.parse(codigo)):
        if isinstance(no, ast.Import):
            importados.update(alias.name.split(".")[0] for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            importados.add(no.module.split(".")[0])
    return importados


# ----- A fronteira do projeto -----


def test_as_regras_nao_dependem_de_pygame():
    """Nem `jogo.py` nem `palavras.py` podem importar pygame.

    Por quê: é a regra de ouro deste projeto — as regras têm de rodar sem abrir janela. E o
    pygame está instalado de qualquer jeito, então um `import pygame` no meio das regras
    deixaria a suíte inteira verde: a fronteira dependeria de alguém reparar no diff.
    """
    for modulo in (modulo_jogo, modulo_palavras):
        assert "pygame" not in modulos_importados_por(modulo), (
            f"{modulo.__name__} passou a importar pygame — leia a regra de ouro no CLAUDE.md"
        )


# ----- Avaliar um chute -----


def test_acertar_a_palavra_deixa_tudo_verde():
    """Chutar a palavra exata pinta as cinco letras de verde — é o fim feliz do jogo."""
    assert marcas("TERMO", "TERMO") == [CERTA] * 5


def test_letra_no_lugar_certo_fica_verde():
    """Letra certa na posição certa é verde, mesmo com o resto do chute errado."""
    assert marcas("TUDOS", "TERMO")[0] is CERTA


def test_letra_que_nao_existe_fica_cinza():
    """Letra que não está na palavra fica cinza — é o que elimina opções."""
    assert marcas("ZZZZZ", "TERMO") == [AUSENTE] * 5


def test_letra_em_outro_lugar_fica_amarela():
    """Letra que existe, mas noutra posição, fica amarela.

    Sem isso o jogo perde a graça: amarelo é a única dica que diz "você está perto".
    """
    assert marcas("OTERM", "TERMO") == [DESLOCADA] * 5


def test_letra_repetida_no_chute_nao_acende_duas_vezes():
    """Chutar a mesma letra duas vezes numa palavra que só tem uma acende apenas uma.

    Por quê: é o erro clássico de quem implementa este jogo num passo só. Em TETRA contra
    TERMO, o primeiro T é verde e o segundo TEM de ser cinza — se os dois acendessem, a
    pessoa concluiria que existem dois Ts na palavra e jogaria a partida inteira errado.
    """
    assert marcas("TETRA", "TERMO") == [CERTA, CERTA, AUSENTE, DESLOCADA, AUSENTE]


def test_letra_repetida_acende_tantas_vezes_quantas_existem():
    """Chutar cinco letras iguais acende só as que a palavra realmente tem.

    Por quê: AMORA tem dois As, nas pontas. Chutar AAAAA tem de devolver exatamente dois
    verdes e três cinzas — nem mais nem menos, senão a contagem de letras está furada.
    """
    assert marcas("AAAAA", "AMORA") == [CERTA, AUSENTE, AUSENTE, AUSENTE, CERTA]


def test_letra_repetida_na_palavra_pode_gerar_dois_amarelos():
    """Quando a palavra tem a letra duas vezes, dois amarelos são legítimos.

    Por quê: o teste acima não pode ser "consertado" limitando a um amarelo por letra.
    Em ALADO contra AMORA, o segundo A é amarelo porque AMORA ainda tem outro A sobrando.
    """
    assert marcas("ALADO", "AMORA") == [CERTA, AUSENTE, DESLOCADA, AUSENTE, DESLOCADA]


def test_chute_de_outro_tamanho_e_recusado():
    """Avaliar um chute de tamanho diferente estoura na hora, em vez de devolver bobagem."""
    with pytest.raises(ValueError):
        avaliar("OI", "TERMO")


# ----- Acentos -----


def test_chute_sem_acento_acerta_palavra_acentuada():
    """Quem digita LICAO acerta LIÇÃO.

    Por quê: o teclado de quem joga nem sempre tem acento fácil, e perder uma das seis
    tentativas por não saber onde vai o til seria castigo por ortografia, não por dedução.
    """
    assert marcas("LICAO", "LIÇÃO") == [CERTA] * 5


def test_acento_aparece_na_tela_quando_a_letra_esta_no_lugar_certo():
    """A letra verde volta acentuada para a tela, como no Termo original."""
    assert exibicao("LICAO", "LIÇÃO") == "LIÇÃO"


def test_letra_amarela_nao_revela_o_acento():
    """Letra amarela aparece sem acento.

    Por quê: mostrar o Ç num quadradinho amarelo entregaria de graça uma informação que o
    jogo original só dá quando você acerta a posição.
    """
    assert exibicao("CALOS", "LIÇÃO") == "CALOS"


# ----- Digitar, apagar e enviar -----


def test_digitar_monta_o_chute_letra_por_letra():
    """Digitar acrescenta ao chute atual — é o gesto principal do jogo."""
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASA")
    assert jogo.digitando == ["C", "A", "S", "A", ""]


def test_digitar_aceita_letra_acentuada_do_teclado():
    """Quem tem teclado ABNT e digita ç ou á vê a letra sem acento no quadradinho."""
    jogo = Jogo("TERMO")
    jogo.digitar("ç")
    jogo.digitar("á")
    assert chute_visivel(jogo) == "CA___"


def test_digitar_ignora_tecla_que_nao_e_letra():
    """Número, espaço e pontuação não entram no chute — senão a grade mostraria lixo.

    A casa selecionada também não anda: tecla recusada não pode mover a seleção, ou a
    próxima letra cairia num lugar que a pessoa não escolheu.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "1 -%")
    assert chute_visivel(jogo) == "_____"
    assert jogo.cursor == 0


def test_nao_da_para_digitar_a_sexta_letra():
    """O chute para na quinta letra: a palavra tem cinco, e a grade também.

    Por quê: com a linha cheia não sobra casa vazia, e a seleção sai da linha. Se ela
    ficasse na última casa, encostar numa tecla a mais trocaria a quinta letra sem a pessoa
    perceber — e ela mandaria, gastando uma tentativa, uma palavra que não quis chutar.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CARROS")
    assert chute_visivel(jogo) == "CARRO"
    assert jogo.cursor == CURSOR_FIM_DA_LINHA


def test_digitar_anda_para_a_proxima_casa_vazia():
    """Escrita uma letra, a seleção pula sozinha para a próxima casa ainda vazia.

    Por quê: é o que faz digitar as cinco letras seguidas continuar funcionando como sempre,
    agora que dá para escolher a casa. Sem isso, a pessoa teria de clicar a cada letra.
    """
    jogo = Jogo("TERMO")
    jogo.digitar("C")
    assert jogo.cursor == 1


def test_digitar_numa_casa_ja_ocupada_troca_a_letra():
    """Escolher uma casa que já tem letra e digitar substitui a letra que estava lá.

    Por quê: é o ponto inteiro desta feature — trocar o começo da palavra sem ter de apagar
    as quatro letras que vieram depois dele.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASAL")
    jogo.selecionar(0)
    jogo.digitar("M")
    assert chute_visivel(jogo) == "MASAL"


def test_cursor_volta_para_a_casa_vazia_que_ficou_para_tras():
    """Com um buraco no meio, preencher a última casa leva a seleção de volta ao buraco.

    Por quê: quem deixou um buraco quer preenchê-lo. Se a seleção parasse no fim da linha, a
    pessoa apertaria Enter e ouviria "faltam letras" sem o jogo mostrar onde falta.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASAL")
    jogo.selecionar(1)
    jogo.apagar()
    jogo.selecionar(4)
    jogo.digitar("R")
    assert chute_visivel(jogo) == "C_SAR"
    assert jogo.cursor == 1


def test_seta_escolhe_a_casa_do_lado():
    """As setas andam com a casa selecionada, uma de cada vez.

    Por quê: é a alternativa ao mouse. Sem ela, quem joga só de teclado não alcança a feature.
    """
    jogo = Jogo("TERMO")
    jogo.mover_cursor(1)
    jogo.mover_cursor(1)
    jogo.digitar("A")
    assert chute_visivel(jogo) == "__A__"


def test_setas_param_nas_pontas_da_linha():
    """Na primeira casa a seta da esquerda não faz nada, e na última a da direita também.

    Por quê: a grade tem começo e fim à vista. Uma seleção que salta do fim para o começo
    parece defeito, e faz a pessoa apagar a letra errada sem entender por quê.
    """
    jogo = Jogo("TERMO")
    jogo.mover_cursor(-1)
    assert jogo.cursor == 0
    for _ in range(TAMANHO_PALAVRA + 2):
        jogo.mover_cursor(1)
    assert jogo.cursor == TAMANHO_PALAVRA - 1


def test_selecionar_casa_que_nao_existe_e_ignorado():
    """Pedir uma casa fora das cinco não muda a seleção nem estoura.

    Por quê: quem chama é a tela, a partir de um clique que pode ter caído em qualquer canto
    da janela. E um número negativo, em Python, escolheria a casa do fim em silêncio.
    """
    jogo = Jogo("TERMO")
    jogo.selecionar(-1)
    jogo.selecionar(TAMANHO_PALAVRA)
    assert jogo.cursor == 0


def test_apagar_remove_a_ultima_letra():
    """Backspace desfaz a última letra — é como a pessoa corrige um erro de digitação."""
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASA")
    jogo.apagar()
    assert chute_visivel(jogo) == "CAS__"


def test_apagar_limpa_a_casa_selecionada():
    """Backspace com uma casa escolhida apaga a letra daquela casa, e só ela.

    Por quê: sem isso, corrigir o meio da palavra ainda exigiria apagar tudo o que veio
    depois — que é justamente o incômodo que esta feature resolve.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASAL")
    jogo.selecionar(2)
    jogo.apagar()
    assert chute_visivel(jogo) == "CA_AL"
    assert jogo.cursor == 2


def test_apagar_em_casa_vazia_apaga_a_letra_de_tras():
    """Com a casa selecionada já vazia, Backspace desfaz a letra anterior, como sempre fez.

    Por quê: é assim que a pessoa apaga um chute inteiro no tapa, letra por letra. Se ele só
    limpasse a casa vazia, não faria nada e pareceria quebrado.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CAS")
    jogo.apagar()
    jogo.apagar()
    assert chute_visivel(jogo) == "C____"


def test_chute_incompleto_nao_gasta_tentativa():
    """Enter com o chute pela metade avisa e não consome uma das seis chances.

    Por quê: apertar Enter cedo demais é escorregão de dedo, não jogada. Gastar tentativa
    por isso faria a pessoa perder a partida sem ter errado nenhum palpite.
    """
    jogo = Jogo("TERMO")
    jogo.digitar("A")
    assert jogo.enviar() is False
    assert jogo.tentativas == []
    assert jogo.aviso == AVISO_FALTAM_LETRAS
    assert chute_visivel(jogo) == "A____"


def test_chute_com_buraco_no_meio_nao_e_aceito():
    """Enter com uma casa vazia no meio avisa e também não gasta tentativa.

    Por quê: agora a linha sempre tem cinco casas, então contar letras não basta — a
    pergunta certa passou a ser se sobrou buraco. Sem esta checagem, a casa vazia viraria
    uma letra fantasma na avaliação e a grade mostraria um quadradinho colorido sem letra.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASAL")
    jogo.selecionar(2)
    jogo.apagar()
    assert jogo.enviar() is False
    assert jogo.tentativas == []
    assert jogo.aviso == AVISO_FALTAM_LETRAS


def test_enviar_guarda_a_tentativa_e_limpa_o_que_estava_digitado():
    """Depois de enviar, a linha vira histórico e a próxima começa vazia."""
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASAL")
    assert jogo.enviar() is True
    assert len(jogo.tentativas) == 1
    assert chute_visivel(jogo) == "_____"


def test_enviar_devolve_a_selecao_para_a_primeira_casa():
    """Mandado o chute, a linha nova começa com a primeira casa selecionada.

    Por quê: assim a pessoa continua digitando a palavra seguinte sem tocar no mouse.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "CASAL")
    jogo.selecionar(3)
    jogo.enviar()
    assert jogo.cursor == 0


# ----- Fim de partida -----


def test_acertar_termina_a_partida_com_vitoria():
    """Acertar encerra a partida na hora, mesmo sobrando tentativa."""
    jogo = Jogo("TERMO")
    for tecla in "TERMO":
        jogo.digitar(tecla)
    jogo.enviar()
    assert jogo.situacao is Situacao.VITORIA
    assert jogo.acabou


def test_errar_todas_as_tentativas_termina_em_derrota_e_revela_a_palavra():
    """Na sexta errada o jogo acaba e conta qual era a palavra.

    Por quê: terminar sem revelar deixa a pessoa sem aprender nada com a derrota — e a
    palavra secreta não tem mais nenhum valor depois do fim.
    """
    jogo = Jogo("TERMO")
    for _ in range(MAXIMO_TENTATIVAS):
        for tecla in "CASAL":
            jogo.digitar(tecla)
        jogo.enviar()
    assert jogo.situacao is Situacao.DERROTA
    assert "TERMO" in jogo.aviso


def test_partida_acabada_ignora_o_teclado():
    """Depois do fim, digitar e enviar não fazem nada — a grade fica congelada."""
    jogo = Jogo("TERMO")
    for tecla in "TERMO":
        jogo.digitar(tecla)
    jogo.enviar()

    jogo.digitar("A")
    jogo.apagar()
    assert chute_visivel(jogo) == "_____"
    assert jogo.enviar() is False
    assert len(jogo.tentativas) == 1


def test_partida_acabada_ignora_o_mouse_e_as_setas():
    """Depois do fim, clicar numa casa e apertar as setas não mexem na seleção.

    Por quê: a grade congela ao acabar a partida. Uma casa que ainda responde ao clique faz
    a pessoa achar que dá para continuar chutando.
    """
    jogo = Jogo("TERMO")
    digitar_tudo(jogo, "TERMO")
    jogo.enviar()

    jogo.selecionar(3)
    jogo.mover_cursor(1)
    assert jogo.cursor == 0


def test_tentativas_restantes_diminui_a_cada_chute():
    """O contador de chances reflete o que já foi gasto."""
    jogo = Jogo("TERMO")
    assert jogo.tentativas_restantes == MAXIMO_TENTATIVAS
    for tecla in "CASAL":
        jogo.digitar(tecla)
    jogo.enviar()
    assert jogo.tentativas_restantes == MAXIMO_TENTATIVAS - 1


def test_reiniciar_limpa_a_grade():
    """Reiniciar devolve uma partida zerada, pronta para o primeiro chute."""
    jogo = Jogo("TERMO")
    for tecla in "CASAL":
        jogo.digitar(tecla)
    jogo.enviar()
    jogo.reiniciar()
    assert jogo.tentativas == []
    assert chute_visivel(jogo) == "_____"
    assert jogo.situacao is Situacao.JOGANDO


def test_reiniciar_devolve_a_selecao_para_a_primeira_casa():
    """Partida nova começa com a primeira casa selecionada, como a primeira de todas."""
    jogo = Jogo("TERMO")
    jogo.selecionar(4)
    jogo.reiniciar()
    assert jogo.cursor == 0


def test_palavra_secreta_de_tamanho_errado_e_recusada():
    """Começar uma partida com palavra que não tem 5 letras falha na hora.

    Por quê: a grade tem cinco colunas. Uma palavra de seis letras só apareceria como bug
    estranho no meio do jogo, e o erro aqui diz exatamente o que está errado.
    """
    with pytest.raises(ValueError):
        Jogo("PALAVRA")


def test_palavra_escrita_com_acento_solto_e_arrumada():
    """Palavra com o acento separado da letra é normalizada ao começar a partida.

    Por quê: LIÇÃO pode vir escrito com o Ç inteiro ou com um C seguido de uma cedilha solta —
    parecem iguais na tela, mas o segundo tem 7 caracteres, e a grade mostraria um acento
    sozinho num quadradinho. Isso acontece de verdade ao colar uma lista de palavras da
    internet.
    """
    jogo = Jogo(unicodedata.normalize("NFD", "LIÇÃO"))
    assert jogo.secreta == "LIÇÃO"
    assert len(jogo.secreta) == TAMANHO_PALAVRA


# ----- Teclado da tela -----


def test_teclado_guarda_a_melhor_marca_de_cada_letra():
    """Uma letra que já ficou verde não volta a amarelo num chute posterior.

    Por quê: o teclado colorido é um resumo do que já se sabe. Se o T rebaixasse de verde
    para amarelo, a pessoa acharia que tinha errado a posição que já tinha acertado.
    """
    jogo = Jogo("TERMO")
    for tecla in "TECLA":
        jogo.digitar(tecla)
    jogo.enviar()
    assert jogo.letras_usadas()["T"] is CERTA

    for tecla in "MOTOR":
        jogo.digitar(tecla)
    jogo.enviar()
    assert jogo.letras_usadas()["T"] is CERTA
    assert jogo.letras_usadas()["C"] is AUSENTE
