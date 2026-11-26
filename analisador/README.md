# Analisadores Léxico e Sintático

Implementação, em Python 3 (sem bibliotecas externas), do analisador léxico e do
analisador sintático para a gramática LL(1) da dupla (`../gramatica/gramatica.bnf`).
Cada decisão também está explicada nos comentários do próprio código.

## Sumário

1. [Como executar](#1-como-executar)
2. [Arquivos](#2-arquivos)
3. [Visão geral](#3-visão-geral)
4. [Como construímos o analisador léxico](#4-como-construímos-o-analisador-léxico)
5. [Como construímos o analisador sintático](#5-como-construímos-o-analisador-sintático)
6. [Exemplo passo a passo](#6-exemplo-passo-a-passo)
7. [O que fica para a análise semântica](#7-o-que-fica-para-a-análise-semântica)
8. [Como verificamos](#8-como-verificamos)

---

## 1. Como executar

Dentro da pasta `analisador`:

```bash
python main.py ../gramatica/exemplos/valido.txt              # analisa o programa
python main.py ../gramatica/exemplos/valido.txt --tokens     # + lista de tokens
python main.py ../gramatica/exemplos/valido.txt --arvore     # + árvore de derivação
python testes.py                                             # roda todos os testes
```

Saída para um programa correto:

```
../gramatica/exemplos/valido.txt: programa aceito (léxica e sintaticamente correto)
```

Saída para um programa com erro (o analisador para no primeiro erro):

```
programa.txt: Erro léxico (linha 5, coluna 5): '=' sozinho não existe: use ':=' para atribuição ou '==' para comparação
programa.txt: Erro sintático (linha 5, coluna 17): esperado 'begin', encontrado 'x'
```

---

## 2. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `tokens.py` | Tipos de token, tabela de palavras reservadas e tabela de símbolos |
| `erros.py` | Exceções `ErroLexico` e `ErroSintatico` (com linha e coluna) |
| `lexico.py` | **Analisador léxico**: transforma o texto em tokens |
| `sintatico.py` | **Analisador sintático** descendente recursivo preditivo |
| `main.py` | Programa principal (lê o arquivo e chama os analisadores) |
| `testes.py` | Testes: um programa aceito para cada requisito, erros léxicos, erros sintáticos e os exemplos de `../gramatica/exemplos` |

---

## 3. Visão geral

```
código-fonte ──► AnalisadorLexico ──(um token por vez)──► AnalisadorSintatico ──► aceito / erro
                  proximo_token()                          um método por não-terminal
```

- O **léxico** lê caracteres e os agrupa em *tokens*, como `ID(x)`, `:=` e `NUM(10)`.
  Ele descarta espaços e comentários.
- O **sintático** confere se a sequência de tokens segue a gramática.
- O sintático pede um token de cada vez ao léxico (`proximo_token()`), como na Fig. 3.1
  do livro. O token atual é o **lookahead**: o único token que o sintático olha para
  decidir o que fazer.

Essa divisão segue o livro (Seção 4.3, p. 77). A estrutura léxica (identificadores,
números, palavras-chave) é simples e é tratada no léxico. A gramática trabalha só com
tokens, por isso aparecem nela `ID` e `NUM` no lugar dos caracteres.

---

## 4. Como construímos o analisador léxico

### Passo 1 — Levantar os tokens a partir da gramática (`tokens.py`)

Listamos todos os **terminais** de `gramatica.bnf` e criamos um tipo de token para cada
um (`TipoToken`):

| Grupo | Tokens |
|---|---|
| Com lexema variável | `ID`, `NUM` |
| Palavras reservadas | `program var integer boolean procedure function begin end if then else while do return break continue print true false` |
| Símbolos de 2 caracteres | `:=  ==  !=  >=  <=` |
| Símbolos de 1 caractere | `>  <  +  -  *  /  (  )  ,  ;  :  .` |
| Fim da entrada | `EOF` (o `$` do livro) |

**Decisão:** cada terminal tem o seu próprio tipo, em vez de tipos genéricos como
"OPERADOR". Assim o sintático compara tipos diretamente, do mesmo jeito que estão nas
produções.

Cada token guarda `tipo`, `lexema` (o texto lido), `linha` e `coluna`. A linha e a
coluna servem para as mensagens de erro.

### Passo 2 — Definir a forma de cada token

São as definições regulares da seção 6 de `gramatica.bnf`:

```
ID   = letra ( letra | dígito | "_" )*
NUM  = dígito dígito*
```

Palavras reservadas e símbolos têm forma fixa. Espaços em branco (espaço, tabulação,
quebra de linha) e comentários `{ ... }` não são tokens: são descartados.

### Passo 3 — Decidir o token pelo primeiro caractere

Como num diagrama de transições (livro, Seção 3.4), o primeiro caractere já diz que tipo
de token está começando. É a lógica de `proximo_token()`:

```
               ┌─ letra ──► lê letras, dígitos e "_" ──► consulta a tabela ──► palavra reservada ou ID
               │
pula espaços   ├─ dígito ─► lê dígitos ──► NUM   (erro se vier letra logo depois: "12abc")
e comentários ─┤
               ├─ outro ──► olha 2 caracteres: ":=" "==" "!=" ">=" "<=" ?
               │              sim ──► símbolo de 2 caracteres
               │              não ──► símbolo de 1 caractere?  sim ──► símbolo
               │                                               não ──► ERRO LÉXICO
               │
               └─ fim do texto ──► EOF
```

### Passo 4 — Regras que resolvem os casos ambíguos

- **Maior lexema possível.** O léxico sempre lê o token mais longo que consegue.
  - `:=` vira um token só, e não `:` seguido de `=`. Por isso os símbolos de 2
    caracteres são testados antes dos de 1.
  - `whilex` é o identificador `whilex`, e não `while` seguido de `x`. Por isso o léxico
    lê o identificador inteiro antes de olhar a tabela.
- **Palavras reservadas por tabela** (livro, Seção 3.4). Palavras reservadas e
  identificadores são lidos pelo mesmo código. No fim, o lexema é procurado em
  `PALAVRAS_RESERVADAS`: se estiver lá, é palavra reservada; senão, é `ID`. Isso evita
  um autômato separado para cada palavra-chave.
- **Maiúsculas e minúsculas são diferentes.** `begin` é palavra reservada; `Begin` é
  identificador.
- **Comentários não são aninhados.** O primeiro `}` fecha o comentário, como no Pascal.

### Passo 5 — Posição e erros

- `_avancar()` consome um caractere e atualiza `linha` e `coluna`. Cada `\n` soma 1 na
  linha e volta a coluna para 1.
- Antes de ler um token, o léxico anota onde ele começa. Essa posição vai para o token.
- **Erros léxicos** (o léxico para e mostra linha e coluna):

| Situação | Exemplo |
|---|---|
| Caractere fora da linguagem | `@`, `#`, `ç` fora de comentário |
| `=` ou `!` sozinhos | `x = 1` (o certo é `:=` ou `==`) |
| Número colado em letra | `12abc` |
| Identificador começando com `_` | `_x` |
| Comentário aberto e não fechado | `{ sem fim` (aponta a linha do `{`) |
| `}` sem `{` | `x := 1; }` |

As letras são conferidas manualmente (`a`-`z`, `A`-`Z`), e não com `isalpha()` do
Python, que aceitaria letras acentuadas.

### Passo 6 — Ligação com o sintático

O léxico tem dois métodos públicos:

- `proximo_token()` lê e devolve **um** token. É o que o sintático usa: o texto é
  percorrido uma única vez, sob demanda.
- `tokenizar()` devolve a lista inteira de tokens. Só é usado para exibir os tokens
  (`--tokens`).

---

## 5. Como construímos o analisador sintático

### Passo 1 — Partir da gramática LL(1)

O ponto de partida é `gramatica.bnf`, que já está:

- **sem recursão à esquerda.** Senão, um método chamaria a si mesmo sem consumir nada:
  laço infinito (livro, p. 81).
- **fatorada à esquerda.** Senão, duas alternativas começariam com o mesmo token e não
  daria para escolher.
- **sem ambiguidade.**

Por isso basta **1 token de lookahead** e o analisador nunca precisa voltar atrás
(retrocesso).

### Passo 2 — Calcular PRIMEIRO e SEGUINTE

Os conjuntos da tabela da seção 5.4 de `gramatica/README.md` viraram constantes no topo
de `sintatico.py` (`PRIMEIRO_COMANDO`, `PRIMEIRO_EXPRESSAO`, `SEGUINTE_LISTA_COMANDOS`,
...). Eles são usados para decidir as alternativas ε (passo 4).

### Passo 3 — Traduzir cada produção em um método

Regra de tradução usada em **todas** as produções (livro, Seção 2.4 e 4.4):

| Na produção | No código |
|---|---|
| Não-terminal `<x>` | Um método `x()`; usar `<x>` no lado direito = chamar `self.x()` |
| Terminal `"t"` | `self._consumir(T.T)`: confere se o token atual é `t` e pede o próximo ao léxico |
| Alternativas que começam com terminais diferentes | `if`/`elif` olhando o token atual (`self.atual.tipo`) |
| Alternativa ε | `if self._usa_alternativa(PRIMEIRO, SEGUINTE):` (passo 4) |

Exemplo, lado a lado:

```
<comando_enquanto> ::= "while" <expressao> "do" <comando_composto>
```

```python
def comando_enquanto(self):
    self._consumir(T.WHILE)
    self.expressao()
    self._consumir(T.DO)
    self.comando_composto()
```

Exemplo com alternativas diferentes:

```
<tipo> ::= "integer" | "boolean"
```

```python
def tipo(self):
    if self.atual.tipo == T.INTEGER:
        self._consumir(T.INTEGER)
    elif self.atual.tipo == T.BOOLEAN:
        self._consumir(T.BOOLEAN)
    else:
        self._erro({T.INTEGER, T.BOOLEAN})
```

São 43 não-terminais e 43 métodos. A produção de cada um está copiada no comentário do
método, então o código pode ser lido lado a lado com `gramatica.bnf`.

### Passo 4 — Decidir as alternativas ε com PRIMEIRO e SEGUINTE

Em uma produção `A ::= α | ε`, o método `_usa_alternativa(primeiro, seguinte)` faz o
mesmo que a tabela sintática do Algoritmo 4.4 do livro:

| Token atual | Decisão |
|---|---|
| está em PRIMEIRO(α) | segue α |
| está em SEGUINTE(A) | usa ε (não consome nada) |
| qualquer outro | **erro**, listando PRIMEIRO ∪ SEGUINTE como esperados |

Exemplo:

```
<resto_termo> ::= <operador_multiplicativo> <fator> <resto_termo> | ε
```

```python
def resto_termo(self):
    if self._usa_alternativa(OPERADORES_MULTIPLICATIVOS, SEGUINTE_RESTO_TERMO):
        self.operador_multiplicativo()
        self.fator()
        self.resto_termo()
```

**Decisão:** conferir o SEGUINTE, em vez de simplesmente usar ε sempre que o token não
estiver em PRIMEIRO, faz o erro ser detectado no ponto mais cedo possível e com a lista
exata do que era esperado.

As listas (`<mais_identificadores>`, `<lista_comandos>`, ...) são implementadas com
recursão **à direita**, igual à gramática. Isso não causa laço infinito, porque cada
chamada consome pelo menos um token antes de chamar a si mesma.

### Passo 5 — Pontos que dependem da fatoração e da ambiguidade

| Situação | Como o código resolve |
|---|---|
| Atribuição × chamada de procedimento (ambas começam com `ID`) | `comando_identificador()` consome o `ID`; `resto_comando_identificador()` decide pelo próximo token: `:=` é atribuição, `(` é chamada |
| Variável × chamada de função (ambas começam com `ID`) | `fator()` consome o `ID`; `resto_fator()` decide: `(` é chamada, senão é variável (ε) |
| `else` pendente | o corpo do `if` é sempre `comando_composto()` (`begin ... end`), então o `else` só pode vir depois do `end` deste `if` |
| `a < b < c` | `resto_expressao()` aceita **um** relacional e não chama a si mesma; o segundo `<` não está em SEGUINTE, então é erro |
| `-` unário × `-` binário | o unário fica em `fator()` (início de fator); o binário em `resto_expressao_simples()` (depois de um termo) |

### Passo 6 — Início, fim e erros

- `analisar()` chama `programa()` (o símbolo de partida) e depois exige `EOF`. Assim,
  nada pode vir depois do `.` final.
- Em qualquer erro, `_erro()` lança `ErroSintatico` com a linha e a coluna do token
  atual, o token encontrado e os tokens que eram esperados.
- **Decisão:** parar no primeiro erro. Mantém o código simples e a mensagem sempre
  correta. O livro descreve recuperação de erros (Seção 4.4, "modalidade do
  desespero"), que poderia ser acrescentada depois.
- O erro é apontado **onde é descoberto**, que às vezes é depois de onde está o engano.
  Num `;` esquecido no fim da linha 4, o erro aparece no primeiro token da linha 5.

### Passo 7 — Rastreamento (árvore de derivação)

Cada método é envolvido por `with self._regra("<nome>"):`. Com `--arvore`, isso imprime
cada não-terminal expandido, cada terminal consumido e cada ε, com recuo. O resultado é
a árvore de derivação que o analisador percorre. Serve para entender e apresentar o
funcionamento.

---

## 6. Exemplo passo a passo

Analisando o comando `x := a + 1;` dentro de um `begin ... end`:

| Token atual | Método | Decisão |
|---|---|---|
| `ID(x)` | `lista_comandos()` | `ID` está em PRIMEIRO(`<comando>`), então há mais um comando |
| `ID(x)` | `comando()` | `ID` escolhe a alternativa `<comando_identificador> ";"` |
| `ID(x)` | `comando_identificador()` | consome `x` |
| `:=` | `resto_comando_identificador()` | `:=` indica atribuição; consome `:=` |
| `ID(a)` | `expressao()` → `expressao_simples()` → `termo()` → `fator()` | `ID`: consome `a` |
| `+` | `resto_fator()` | `+` está em SEGUINTE e não é `(`, então usa ε (é variável, não chamada) |
| `+` | `resto_termo()` | `+` não é `*` nem `/`, mas está em SEGUINTE, então usa ε |
| `+` | `resto_expressao_simples()` | `+` está em PRIMEIRO, então consome `+` e chama `termo()` |
| `NUM(1)` | `fator()` | `NUM`: consome `1` |
| `;` | `resto_termo()`, `resto_expressao_simples()`, `resto_expressao()` | `;` está no SEGUINTE de todos, então usam ε |
| `;` | `comando()` | consome o `;` que termina o comando simples |

Para ver isso na tela, rode com `--arvore`.

---

## 7. O que fica para a análise semântica

A gramática e o sintático verificam só a **forma** do programa. Estas verificações
precisam de informações que uma gramática livre de contexto não guarda (livro, Exemplo
4.12) e ficam para a próxima etapa:

- variável ou sub-rotina declarada antes do uso;
- tipos compatíveis (ex.: somar `boolean` com `integer`);
- número de argumentos igual ao de parâmetros;
- `return` só dentro de função;
- `break` e `continue` só dentro de `while`;
- valor de um número cabe em um inteiro.

---

## 8. Como verificamos

- **`testes.py`:** um programa aceito para cada um dos 11 requisitos, além de casos de
  erro léxico, casos de erro sintático e os exemplos de `../gramatica/exemplos` (o
  válido deve ser aceito e os inválidos rejeitados).
- **Comparação com um analisador gerado da gramática:** geramos automaticamente, a
  partir de `gramatica.bnf`, um analisador de tabela LL(1) (Algoritmos 4.3 e 4.4 do
  livro). Criamos 3000 programas alterando aleatoriamente o `valido.txt` e passamos
  todos pelos dois analisadores. Os dois aceitaram e rejeitaram exatamente os mesmos
  programas, o que indica que o analisador escrito à mão segue fielmente a gramática.
