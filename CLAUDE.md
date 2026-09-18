# CLAUDE.md — manual do Claude Code para este projeto

## Sobre este projeto

Jogo do **Termo**: descobrir uma palavra de 5 letras em até 6 tentativas, com a grade de
quadradinhos verdes, amarelos e cinzas. Python 3.12, `pygame-ce`, dependências com `uv`.

Ele é material didático da **39A**: pessoas **não técnicas** forkam este repositório e usam você,
Claude Code, para acrescentar features e modos novos. O jogo base já funciona e tem testes.

Isso muda o seu trabalho aqui: quem te guia não sabe programar, não vai ler o diff, não vai revisar
seu código e não vai perceber se você quebrou algo. **Você é, ao mesmo tempo, quem programa, quem
revisa e quem lembra por que as coisas são como são.** Os testes, o ruff, o `DECISOES.md` e a
arquitetura simples são a rede de segurança — trate-os como sagrados.

## O plugin `engenharia@39a` é o caminho

Este repositório foi feito para ser usado **com o plugin de engenharia da 39A**. Ele carrega o padrão
técnico da casa, e aprender a chamar a skill certa é metade do que se aprende aqui. **Consulte a
skill antes de escrever código**, não depois.

| A pessoa quer                                      | Skill                        |
| -------------------------------------------------- | ---------------------------- |
| Acrescentar ou mudar alguma coisa no jogo          | `/nova-feature`              |
| Conferir se está tudo certo (testes e qualidade)   | `/verificar`                 |
| Revisar o que foi feito, antes de commitar ou abrir PR | `/revisar`               |
| Entender um erro que apareceu                      | `/investigar`                |
| Não sabe o que pedir nem qual skill usar           | subagent `engenharia:guia-39a` |
| Máquina nova, ou falta uma ferramenta              | `/setup-inicial`             |

**Seja honesto sobre o que não se aplica.** Este jogo não tem servidor, banco de dados, fila nem
infraestrutura: `/deploy`, `/custos`, `/consultar-dados`, `/restaurar-dado`, `/acessar` e
`/acesso-de-pessoa` não têm o que fazer aqui, e `/rodar-local` fala de Postgres e API — aqui rodar é
`uv run termo`. Mandar a pessoa para uma skill que não serve é pior do que não sugerir nenhuma:
manda para o lugar errado com ar de autoridade.

Se o plugin não estiver instalado na sessão, diga isso em vez de fingir que chamou a skill — e veja
[Se você não tem o plugin](#se-você-não-tem-o-plugin) no fim deste arquivo.

## Como você deve trabalhar aqui

1. **Fale em português simples.** Antes de mexer, diga em 1–2 frases o que vai fazer. Depois, resuma
   o que mudou e **como a pessoa vê o resultado** (ex.: "abra o jogo com `uv run termo` e digite uma
   palavra com duas letras iguais"). Sem jargão gratuito: em vez de "refatorei o loop de
   renderização", diga "mudei a parte que desenha a grade".
2. **Uma feature por vez, em passos pequenos.** Se o pedido for grande ("quero o modo dueto com
   ranking"), proponha quebrar em partes e comece pela menor que já dá para ver funcionando.
3. **Só diga "pronto" depois do Checklist de Pronto** (abaixo). Se algo quebrou, conserte antes de
   avisar.
4. **Você não abre janela.** `uv run termo` segura o terminal até a pessoa fechar o jogo — quem roda
   é ela. Peça para ela rodar e **diga exatamente o que tem de aparecer na tela**. Para conferir
   sozinho, use os testes: eles desenham a janela em memória, sem abrir nada.
5. **Dependência nova entra com `uv add`**, nunca com `pip install`, e só depois de você explicar
   para que serve. Menos biblioteca é menos coisa para quebrar na máquina de quem está aprendendo.
6. **Pedido ambíguo → UMA pergunta curta**, já com uma sugestão de resposta. Não faça interrogatório.
7. **Não mude a arquitetura básica** (`jogo.py` ↔ `gui.py`), não troque de biblioteca gráfica nem de
   gerenciador de pacotes sem a pessoa confirmar explicitamente.
8. **Tudo em português**: textos da tela, nomes de função, de variável, de teste e os comentários.
   Ver [Convenções de código](#convenções-de-código).
9. **Nunca mexa na lista de palavras para fazer um teste passar.** Se `test_palavras.py` reclamou, é
   porque a palavra está fora de ordem, repetida ou não tem 5 letras — conserte a palavra.

## Git: fork, branch e PR

Este repositório é a base do workshop e fica limpo. **Cada pessoa trabalha no próprio fork**, e é lá
que o trabalho entra — nunca no repositório da 39A.

O fluxo é o mesmo da casa, e é de propósito: é o hábito que a pessoa vai levar para o primeiro
projeto de verdade.

```bash
git checkout -b feature/AAAAMMDD-descricao-curta
```

```bash
git push -u origin feature/AAAAMMDD-descricao-curta
```

```bash
gh pr create --base main --repo <usuario>/termo-game --title "..." --body "..."
```

- **O `--repo` não é enfeite.** Dentro de um fork, `gh pr create` propõe o repositório pai por
  padrão — sem ele, a pessoa abre um PR na 39A sem querer.
- **Não commite nem faça push por conta própria.** Pergunte antes. Ler (`git status`, `git diff`,
  `git log`) pode sempre.
- **Mensagem de commit em português**, dizendo o que passa a existir ("mostra as letras já usadas no
  teclado"), não o que você fez no código.

## Você também é o revisor

- **Rode `uv run pytest -q` no começo da sessão.** Se já estiver vermelho, conserte antes de
  acrescentar qualquer coisa — senão você não sabe o que foi você que quebrou.
- **Revise de verdade antes de dizer "pronto".** Passe pelo Checklist de Pronto item por item,
  olhando o diff. A skill `/revisar` faz isso de forma guiada — use ao terminar algo maior.
- **Refatorar e implementar são passos separados.** Misturar os dois faz a pessoa não conseguir
  dizer o que aconteceu.
- **Leia o `DECISOES.md` antes de julgar código herdado.** O que parece estranho costuma ter motivo
  escrito lá.

### Checklist de Pronto

1. `uv run ruff format --check .`, `uv run ruff check .` e `uv run pytest -q` **verdes**.
2. Todo comportamento novo tem teste, com docstring explicando **o porquê**. Nenhum teste foi
   apagado, afrouxado ou pulado.
3. `jogo.py` continua sem `pygame`; `gui.py` continua sem regra de jogo; modo novo está em módulo
   próprio.
4. Nada duplicado, nenhuma função gigante, nenhum código morto ou comentado, nenhum `TODO` solto.
5. Tudo em português — textos, nomes e comentários.
6. Documentação em dia: entrada nova no `DECISOES.md`; árvore e tabela "Onde mexer para…" deste
   arquivo, se criou arquivo ou área nova; `IDEIAS.md` marcado com ✅ se concluiu uma ideia.
7. Nenhuma dependência nova sem justificativa no `DECISOES.md`.
8. Resumo para a pessoa: o que mudou e **como ela vê isso na tela**.

## Testes são a memória do projeto

Ninguém aqui vai ler o código. Quando uma regra quebrar daqui a três semanas, a única coisa que vai
explicar por que ela existia é a **docstring do teste**. É por isso que o `ruff` cobra docstring em
toda função, inclusive nos testes.

Eles servem a duas coisas: **regressão** (avisar que algo quebrou) e **intenção** (dizer o que era
para acontecer, e por quê).

### Escrevendo testes

- **Regra do jogo** → `tests/test_jogo.py`, sem pygame.
- **Lista de palavras** → `tests/test_palavras.py`, que olha o arquivo `palavras.txt` de verdade.
- **Tela, tecla, tamanho de janela** → `tests/test_gui_smoke.py`, que desenha em memória.
- **Nome do teste descreve o comportamento**, em português: `test_letra_repetida_no_chute_nao_acende_duas_vezes`.
- **A docstring diz o que a pessoa que joga perderia** se a regra sumisse — não a razão técnica:

```python
def test_chute_incompleto_nao_gasta_tentativa():
    """Enter com o chute pela metade avisa e não consome uma das seis chances.

    Por quê: apertar Enter cedo demais é escorregão de dedo, não jogada. Gastar tentativa
    por isso faria a pessoa perder a partida sem ter errado nenhum palpite.
    """
```

- **Um comportamento por teste.** Teste que verifica cinco coisas não diz qual delas quebrou.
- **Teste estado, não pixel.** "O chute tem três letras" é estável; "o quadradinho está no x=192"
  quebra na primeira mudança de tamanho.

### Corrigindo um bug

1. Escreva primeiro um teste que **falha** reproduzindo o bug.
2. Conserte o código até ele passar.
3. Marque a docstring com `Regressão (AAAA-MM-DD): <o que acontecia>`.

### Quando um teste quebra

1. Leia a docstring: ela diz que regra está protegida.
2. Decida se **o código** está errado (conserte o código) ou se **a regra mudou de propósito** (a
   pessoa pediu a mudança).
3. Se a regra mudou mesmo, atualize o teste **e** escreva a entrada no `DECISOES.md`.
4. **Nunca**, para fazer passar: apagar o teste, marcar `skip`/`xfail`, afrouxar o `assert`, embrulhar
   em `try/except` ou trocar a lógica testada por um dublê.

## Registro de decisões: `DECISOES.md`

É o diário do projeto: **o que** foi decidido, **por quê**, e **qual teste protege**. Sessão nova
começa sem a memória da anterior — esse arquivo é o que atravessa.

- **Leia** antes de mexer em algo que parece estranho: normalmente tem motivo escrito.
- **Escreva** sempre que criar uma feature, mudar ou remover um comportamento, acrescentar uma
  dependência, ou tomar uma decisão que alguém poderia questionar depois.
- Formato: entrada nova **em cima**, título curto com a data, três linhas (`O que`, `Por quê`,
  `Protegido por`), cinco no máximo.

## Sustentabilidade do código

- **Arquivos e funções pequenos.** Passou de ~400 linhas num arquivo ou ~40 numa função? Proponha
  dividir, como passo separado. Um modo de jogo novo nasce no próprio módulo (`estatisticas.py`,
  `dueto.py`, `dicionario.py`), nunca inflando `gui.py` ou `jogo.py`.
- **Uma responsabilidade por módulo.** Regra em módulo puro (testável sem pygame); desenho e teclado
  na tela; arquivo salvo (JSON) em módulo próprio.
- **Zero duplicação.** Copiou um trecho? Vire função.
- **Sem código morto.** Nada de função que ninguém chama nem bloco comentado "para depois" — ideia
  futura vai para o `IDEIAS.md`, que é onde ela é achável.
- **Nomes que explicam.** `tentativas_restantes` vale mais que `n`.
- **Poucas dependências.** Cada uma é mais uma coisa para falhar na máquina de quem está aprendendo.

## Comandos

| Para…                              | Comando                      |
| ---------------------------------- | ---------------------------- |
| Jogar                              | `uv run termo`               |
| Rodar os testes                    | `uv run pytest -q`           |
| Ver a qualidade do código          | `uv run ruff check .`        |
| Conferir a formatação              | `uv run ruff format --check .` |
| Arrumar a formatação               | `uv run ruff format .`       |
| Instalar tudo (primeira vez)       | `uv sync`                    |
| Acrescentar uma biblioteca         | `uv add <nome>`              |

Com o plugin instalado, `/verificar` roda o conjunto e explica o resultado em português.

## Arquitetura

```
src/termo/palavras.py     a lista de palavras, o sorteio e a regra de tirar acento (só texto)
src/termo/jogo.py         as regras: avaliar o chute, contar tentativas, vitória e derrota
src/termo/gui.py          a janela: desenha a grade, o aviso e o teclado, e lê as teclas
src/termo/palavras.txt    as palavras do jogo, uma por linha, em ordem alfabética
src/termo/__main__.py     o "botão de ligar" do jogo
tests/                    testes automáticos: avisam quando algo quebra e explicam por que a regra existe
CLAUDE.md                 este arquivo
DECISOES.md               o diário: o que foi decidido, por quê, e qual teste protege
IDEIAS.md                 lista de features para escolher e vibe codar
```

### Regra de ouro

**`jogo.py` não importa pygame. `gui.py` não decide regra nenhuma.** A tela só pergunta ao `Jogo`
("que letras já foram usadas?", "a partida acabou?", "o que está digitado?") e desenha a resposta. É
isso que permite testar as regras sem abrir janela e trocar a aparência sem mexer nas regras.

`palavras.py` fica na base: `jogo.py` usa dele o sorteio e o `sem_acento`. Ninguém importa `gui.py`,
exceto o `__main__.py`.

### Fluxo de uma tecla

`rodar()` → `pygame.event.get()` → `tratar_evento` → `Jogo.digitar` / `apagar` / `enviar` →
`avaliar()` → `desenhar()` lê o novo estado e pinta.

### `jogo.py` — o que o `Jogo` sabe responder

| Membro                  | Para quê                                                                 |
| ----------------------- | ------------------------------------------------------------------------ |
| `secreta`               | a palavra da partida, com acento                                         |
| `tentativas`            | lista de chutes já enviados; cada um é uma lista de `Letra`              |
| `digitando`             | as cinco casas da linha atual, em lista, com `""` nas que estão vazias   |
| `cursor`                | em qual casa a próxima letra entra (`CURSOR_FIM_DA_LINHA` = linha cheia) |
| `linha_atual`           | qual linha da grade está sendo digitada agora                           |
| `situacao`              | `JOGANDO`, `VITORIA` ou `DERROTA`                                        |
| `aviso`                 | o recado para a tela mostrar                                             |
| `acabou`                | atalho para "a partida terminou"                                         |
| `tentativas_restantes`  | quantas chances sobraram                                                 |
| `letras_usadas()`       | a melhor marca de cada letra, para colorir o teclado                     |
| `digitar` / `apagar` / `enviar` / `reiniciar` | o que a pessoa faz                                 |
| `mover_cursor` / `selecionar` | escolher a casa: `-1`/`+1` (setas) ou o número da casa (clique)    |

`avaliar(chute, secreta)` é função livre: dá para chamar sem criar partida, e é onde mora a regra das
cores. Cada `Letra` tem `letra` (o que aparece na tela) e `marca` (`CERTA`, `DESLOCADA`, `AUSENTE`).

### `gui.py` — estrutura da classe `Tela`

- **Constantes no topo**: tamanhos, cores, textos e o desenho do teclado. É aí que se mexe para
  mudar a aparência.
- **Geometria calculada**: `LARGURA_JANELA` e `ALTURA_JANELA` saem das constantes — mudar o tamanho
  da casa ajusta a janela sozinho.
- **`rodar`** é o loop; **`tratar_evento`** e **`desenhar`** são públicos e podem ser chamados
  isoladamente. É isso que torna o teste da tela possível sem abrir janela.
- **`Tela(jogo)`** aceita um `Jogo` pronto, para o teste saber qual é a palavra secreta.

## Onde mexer para…

| Pedido                                              | Onde mexer                                                                                 |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Trocar as cores ou os textos da tela                | constantes no topo de `gui.py`                                                             |
| Acrescentar palavras ao jogo                        | `src/termo/palavras.txt`, em ordem alfabética. `test_palavras.py` confere tamanho e repetição |
| Mudar quantas tentativas o jogo dá                  | `MAXIMO_TENTATIVAS` em `jogo.py` + conferir a altura da janela (há teste)                   |
| Mudar como uma letra ganha cor                      | `avaliar()` em `jogo.py` + teste novo em `test_jogo.py`                                     |
| Recusar palavra que não existe                      | `Jogo.enviar` + uma lista de palavras aceitas em `palavras.py` + testes                     |
| Guardar estatísticas ou recorde                     | módulo puro novo (`estatisticas.py`, salvando JSON) + testes; a `Tela` só mostra            |
| Modo de jogo novo (dueto, palavra do dia)           | módulo próprio + interruptor na `Tela`. Não infle `jogo.py` nem `gui.py`                    |
| Deixar o teclado da tela clicável                   | `gui.py`: guardar o retângulo de cada tecla e tratar `MOUSEBUTTONDOWN` (a grade já trata: veja `tratar_clique`) |
| Mudar como se escolhe a casa do chute               | `cursor`, `mover_cursor` e `selecionar` em `jogo.py`; `coluna_clicada` e `casa_selecionada` em `gui.py` |
| Animação ao virar os quadradinhos                   | `gui.py`, usando `pygame.time.get_ticks()` — nunca `time.sleep`                             |

## Convenções de código

- **Tudo em português**: nome de módulo, de função, de variável, de teste, docstring e comentário.
  Quem lê este código está aprendendo a programar em português; `avaliar(chute, secreta)` se entende
  na primeira leitura, `evaluate(guess, secret)` não.
- **Type hints em tudo**, inclusive `-> None`.
- **Docstring curta em toda função**, dizendo o que ela faz. Se houver um porquê não óbvio, ele vem
  num parágrafo depois.
- **Constantes em MAIÚSCULAS no topo do arquivo**, agrupadas por comentário-seção.
- **Comentário explica o porquê**, não o que o código já diz.
- **Nunca `print` nem `input`.** Quem fala com a pessoa é a janela.
- **O ruff manda no estilo.** Não discuta formatação: rode `uv run ruff format .`.

## Armadilhas conhecidas

- **`pygame-ce`, nunca `pygame`.** São o mesmo `import pygame`, mas instalar os dois juntos quebra a
  instalação. Se aparecer erro estranho de pygame, `uv sync --reinstall`.
- **A janela não pode passar de 700 px de altura.** Acima disso ela não cabe em notebook de 1366×768
  com a barra de tarefas, e o teclado some embaixo da barra. Há teste.
- **Texto do aviso não pode passar da largura da janela** — aparece cortado nas duas pontas. Há teste,
  e ele usa a palavra mais larga da lista.
- **`uv run termo` segura o terminal.** Quem roda é a pessoa; você confere pelos testes.
- **Letra repetida é o bug clássico deste jogo.** A avaliação é feita em dois passos (primeiro as
  certas, depois as deslocadas, consumindo o que sobrou). Num passo só, chutar duas letras iguais
  numa palavra que tem uma acende as duas. Há três testes cuidando disso.
- **Acento entra na comparação sem acento e só é revelado na letra certa.** Mexer nisso muda o jogo:
  leia o `DECISOES.md` antes.
- **A lista de palavras tem ordem obrigatória.** Palavra nova vai no lugar alfabético (ignorando o
  acento), senão o teste falha — de propósito, é o que impede a lista de virar bagunça.
- **Nunca edite `.venv/` nem `uv.lock` na mão.** Quem cuida deles é o `uv`.

## Ideias de features

A lista curada, com dificuldade, prompt de exemplo e "onde mexer", está em [`IDEIAS.md`](IDEIAS.md).
Quando a pessoa não souber o que pedir, sugira 2–3 dali e pergunte qual ela quer. Ao concluir uma,
marque-a lá com ✅ no começo do nome.

## Se você não tem o plugin

O plugin `engenharia@39a` mora num marketplace privado da 39A. Quem não tem acesso continua
conseguindo tudo — só sem os atalhos:

| Em vez de    | Rode                                                                    |
| ------------ | ------------------------------------------------------------------------ |
| `/verificar` | `uv run ruff format --check . && uv run ruff check . && uv run pytest -q` |
| `/revisar`   | o Checklist de Pronto deste arquivo, item por item, olhando `git diff`   |

Quem é da 39A instala assim, uma vez:

```
/plugin marketplace add 39A-net-br/claude-plugins-39a
```

```
/plugin install engenharia@39a
```
