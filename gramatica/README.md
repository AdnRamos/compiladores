# Gramática LL(1) – Projeto de Compiladores (UFAPE)

Gramática (BNF) da linguagem do projeto. Ela é **LL(1)** (sem recursão à esquerda,
fatorada à esquerda e com 1 símbolo de look-ahead) e cobre os **11 aspectos** pedidos na
atividade (ver [seção 6](#6-como-cada-requisito-da-atividade-é-atendido)).

A gramática completa e comentada está em `gramatica.bnf`. As técnicas usadas seguem o
livro-texto da disciplina (Aho, Sethi e Ullman, *Compiladores: Princípios, Técnicas e
Ferramentas*). As páginas citadas são as do livro, não as do PDF.

## Sumário

1. [Base teórica](#1-base-teórica)
2. [Legenda da notação](#2-legenda-da-notação)
3. [Exemplo de programa](#3-exemplo-de-programa)
4. [A gramática, produção por produção](#4-a-gramática-produção-por-produção)
5. [Por que a gramática é LL(1)](#5-por-que-a-gramática-é-ll1)
6. [Como cada requisito da atividade é atendido](#6-como-cada-requisito-da-atividade-é-atendido)

---

## 1. Base teórica

| Conceito usado na gramática | Onde está no livro |
|---|---|
| Notação das produções (`→`, `\|`, `ε`, terminais e não-terminais) | Seção 2.2, p. 13 |
| Identificadores e números tratados como *tokens* (`ID`, `NUM`) | Seção 4.3, p. 77; Exemplo 4.11, p. 80 |
| Ambiguidade do `if-then-else` ("else vazio") | Seção 4.3, p. 78-79; Exemplo 4.19, p. 85 |
| Eliminação da recursão à esquerda | Seção 4.3, p. 79; Exemplo 4.8; Algoritmo 4.1 |
| Fatoração à esquerda | Seção 4.3, p. 80; Algoritmo 4.2; Exemplo 4.10 |
| Análise descendente recursiva e analisador preditivo | Seção 4.4, p. 81-82 |
| Conjuntos PRIMEIRO e SEGUINTE (FIRST e FOLLOW) | Seção 4.4, p. 83-84; Exemplo 4.17 |
| Tabela sintática preditiva e definição de gramática LL(1) | Seção 4.4, p. 85; Algoritmo 4.4 |

---

## 2. Legenda da notação

| Símbolo | Significado | No livro |
|---|---|---|
| `<nome>` | Não-terminal | nome em itálico |
| `"texto"` | Terminal (*token*): palavra reservada ou símbolo | negrito |
| `ID` | *Token* identificador (nome de variável, função, procedimento ou programa) | **id** |
| `NUM` | *Token* número inteiro | **num** |
| `::=` | "pode ter a forma" | `→` |
| `\|` | Alternativa ("ou") | `\|` |
| `ε` | Cadeia vazia | `ε` |

Partes opcionais e listas são escritas com `ε` e com recursão **à direita**, no mesmo
formato que o livro usa para eliminar a recursão à esquerda (`A' → αA' | ε`):

```
<lista_identificadores> ::= ID <mais_identificadores>
<mais_identificadores>  ::= "," ID <mais_identificadores> | ε
```

Isso gera `x`, `x, y`, `x, y, z`...

---

## 3. Exemplo de programa

```
program exemplo;
var x: integer;
    ok: boolean;

function dobro(n: integer): integer;
begin
  return n * 2;
end;

begin
  x := dobro(5);
  while x > 0 do
  begin
    if x == 3 then
    begin
      break;
    end
    print(x);
    x := x - 1;
  end
end.
```

---

## 4. A gramática, produção por produção

### 4.1 Estrutura do programa

```
<programa> ::= "program" ID ";" <bloco> "."
<bloco>    ::= <secao_variaveis> <secao_subrotinas> <comando_composto>
```

Um programa tem nome, depois um bloco, e termina com ponto. O bloco tem, **nesta
ordem**: variáveis (opcional), sub-rotinas (opcional) e o corpo principal
(`begin ... end`). `<programa>` é o símbolo de partida.

### 4.2 Declaração de variáveis — requisito 1

```
<secao_variaveis> ::= "var" <declaracao_variaveis> ";" <mais_declaracoes>
                    | ε
<mais_declaracoes> ::= <declaracao_variaveis> ";" <mais_declaracoes>
                     | ε
<declaracao_variaveis>  ::= <lista_identificadores> ":" <tipo>
<lista_identificadores> ::= ID <mais_identificadores>
<mais_identificadores>  ::= "," ID <mais_identificadores>
                          | ε
<tipo> ::= "integer" | "boolean"
```

Exemplo: `var x, y: integer; achou: boolean;`

- Se o próximo *token* é `var`, há variáveis; senão (ε), a seção não existe.
- `<mais_declaracoes>` continua enquanto aparecer um `ID` e para quando aparecer
  `procedure`, `function` ou `begin`.

### 4.3 Procedimentos e funções — requisito 2

```
<secao_subrotinas> ::= <declaracao_subrotina> <secao_subrotinas> | ε
<declaracao_subrotina> ::= <declaracao_procedimento> | <declaracao_funcao>

<declaracao_procedimento> ::= "procedure" ID <parametros_formais> ";" <corpo_subrotina> ";"
<declaracao_funcao>       ::= "function" ID <parametros_formais> ":" <tipo> ";" <corpo_subrotina> ";"

<corpo_subrotina>    ::= <secao_variaveis> <comando_composto>
<parametros_formais> ::= "(" <lista_parametros> ")"
<lista_parametros>   ::= <parametro> <mais_parametros> | ε
<mais_parametros>    ::= "," <parametro> <mais_parametros> | ε
<parametro>          ::= ID ":" <tipo>
```

Exemplos:

```
procedure linha();                                { sem parâmetros }
procedure mostrar(v: integer);                    { com parâmetro }
function dez(): integer;                          { função sem parâmetros }
function maior(a: integer, b: integer): boolean;  { função com parâmetros }
```

- **Procedimento** não retorna valor; **função** declara o tipo de retorno após `:`.
- Os parênteses são **sempre obrigatórios**, mesmo vazios: assim a declaração tem a
  mesma forma da chamada (ver 4.5).
- Sub-rotinas podem ter variáveis locais, mas não sub-rotinas aninhadas
  (`<corpo_subrotina>` não contém `<secao_subrotinas>`).
- Conferir se o número de argumentos de uma chamada bate com o de parâmetros não é
  papel da gramática: o livro mostra que isso nem pode ser expresso por uma gramática
  livre de contexto e fica para a análise semântica (Exemplo 4.12, p. 80).

### 4.4 Comandos

```
<comando_composto> ::= "begin" <lista_comandos> "end"
<lista_comandos>   ::= <comando> <lista_comandos> | ε

<comando> ::= <comando_identificador> ";"
            | <comando_condicional>
            | <comando_enquanto>
            | <comando_retorno> ";"
            | <comando_desvio> ";"
            | <comando_escrita> ";"
            | <comando_composto>
```

**Regra do ponto e vírgula:** comandos simples (atribuição, chamada, `return`,
`break`, `continue`, `print`) **terminam** com `;`. Comandos estruturados (`if`,
`while`, `begin...end`) terminam com `end` e **não** levam `;`.

Como no exemplo do livro (p. 81-82), em que as palavras-chave `if`, `while` e `begin`
indicam qual alternativa de *cmd* usar, cada alternativa de `<comando>` começa com um
*token* diferente:

| Próximo *token* | Comando escolhido |
|---|---|
| `ID` | atribuição ou chamada de procedimento |
| `if` | condicional |
| `while` | laço |
| `return` | retorno |
| `break` / `continue` | desvio incondicional |
| `print` | impressão |
| `begin` | bloco composto |
| `end` | acabou a lista de comandos (ε em `<lista_comandos>`) |

### 4.5 Atribuição e chamada de procedimento — requisitos 3 e 4

```
<comando_identificador>       ::= ID <resto_comando_identificador>
<resto_comando_identificador> ::= ":=" <expressao>
                                | <argumentos>
<argumentos>       ::= "(" <lista_argumentos> ")"
<lista_argumentos> ::= <expressao> <mais_argumentos> | ε
<mais_argumentos>  ::= "," <expressao> <mais_argumentos> | ε
```

Exemplos: `x := y + 1;` `mostrar(x);` `linha();`

Atribuição e chamada **começam com o mesmo *token* (`ID`)**. Escrevendo do jeito
"natural", a gramática não seria LL(1):

```
<comando> ::= ID ":=" <expressao>      { as duas começam com ID: }
            | ID "(" ... ")"           { com 1 token não dá para escolher }
```

Solução: **fatoração à esquerda** (Algoritmo 4.2, p. 80). O prefixo comum `ID` sai em
evidência e a decisão é adiada para o *token* seguinte (`:=` ou `(`).

### 4.6 Condicional (if / else) — requisito 5

```
<comando_condicional> ::= "if" <expressao> "then" <comando_composto> <parte_senao>
<parte_senao> ::= "else" <bloco_senao> | ε
<bloco_senao> ::= <comando_composto> | <comando_condicional>
```

Exemplos:

```
if x > 0 then begin print(x); end

if x == 0 then begin ... end
else begin ... end

if x < 0 then begin ... end
else if x == 0 then begin ... end      { "else if" é permitido }
else begin ... end
```

**Por que o corpo exige `begin ... end`?** O livro mostra (p. 78) que a gramática
`cmd → if expr then cmd | if expr then cmd else cmd | outro` é **ambígua**: a sentença
`if E1 then if E2 then S1 else S2` tem duas árvores gramaticais (Fig. 4.6), porque não
se sabe a qual `then` o `else` pertence. Mesmo depois de fatorada
(`S → iEtSS' | a`, `S' → eS | ε`), ela continua sem ser LL(1): a tabela tem duas
produções na entrada `M[S', e]` (Exemplo 4.19, p. 85).

Exigindo `begin ... end` no corpo, o `else` só pode aparecer logo depois de um `end`
que fecha o `then`, então pertence sem ambiguidade a esse `if`. Formalmente, `else`
não está em SEGUINTE(`<parte_senao>`) (ver tabela da seção 5.4).

### 4.7 Laço while — requisito 6

```
<comando_enquanto> ::= "while" <expressao> "do" <comando_composto>
```

Exemplo: `while i < 10 do begin i := i + 1; end`

### 4.8 Retorno, break e continue — requisitos 7 e 8

```
<comando_retorno> ::= "return" <expressao>
<comando_desvio>  ::= "break" | "continue"
```

- `return <expressao>;` devolve o valor de uma função.
- `break;` sai do laço; `continue;` vai para a próxima iteração.
- A gramática só verifica a **forma**. Regras como "`break` só dentro de `while`" ou
  "`return` só dentro de função" ficam para a análise semântica.

### 4.9 Impressão — requisito 9

```
<comando_escrita> ::= "print" "(" <expressao> ")"
```

Como `<expressao>` inclui constantes e variáveis, valem `print(10);`, `print(true);`,
`print(x);` e até `print(x + 1);`.

### 4.10 Expressões — requisitos 10 e 11

```
<expressao>           ::= <expressao_simples> <resto_expressao>
<resto_expressao>     ::= <operador_relacional> <expressao_simples> | ε
<operador_relacional> ::= "==" | "!=" | ">" | ">=" | "<" | "<="

<expressao_simples>       ::= <termo> <resto_expressao_simples>
<resto_expressao_simples> ::= <operador_aditivo> <termo> <resto_expressao_simples> | ε
<operador_aditivo>        ::= "+" | "-"

<termo>                   ::= <fator> <resto_termo>
<resto_termo>             ::= <operador_multiplicativo> <fator> <resto_termo> | ε
<operador_multiplicativo> ::= "*" | "/"

<fator> ::= ID <resto_fator>
          | NUM
          | "true"
          | "false"
          | "(" <expressao> ")"
          | "-" <fator>
<resto_fator> ::= <argumentos> | ε
```

É a mesma estrutura da gramática de expressões do livro, `E → TE'`, `E' → +TE' | ε`,
`T → FT'`, `T' → *FT' | ε`, `F → (E) | id` (Exemplo 4.8, p. 79), com um nível a mais
para os operadores relacionais:

| Livro (4.11) | Nossa gramática |
|---|---|
| `E` | `<expressao_simples>` |
| `E'` | `<resto_expressao_simples>` |
| `T` | `<termo>` |
| `T'` | `<resto_termo>` |
| `F` | `<fator>` |

**Precedência** (quem está mais "embaixo" na gramática é calculado primeiro):

| Nível | Operadores | Produção |
|---|---|---|
| 1 (maior) | parênteses, `-` unário, chamada de função | `<fator>` |
| 2 | `*` `/` | `<termo>` |
| 3 | `+` `-` | `<expressao_simples>` |
| 4 (menor) | `==` `!=` `>` `>=` `<` `<=` | `<expressao>` |

Assim, `a + b * c > 10` é lido como `(a + (b * c)) > 10`.

- O relacional aparece **no máximo uma vez** por expressão: `a < b < c` não é aceito
  (com parênteses é: `(a < b) == ok`).
- Em `<fator>`, `ID` sozinho é variável e `ID(...)` é chamada de função. De novo,
  resolvido por fatoração (`<resto_fator>`).
- `-` aparece como unário em `<fator>` (`-x`) e como binário em `<operador_aditivo>`
  (`a - b`). Não há conflito: o binário só é esperado **depois** de um termo; o
  unário, **no início** de um fator.

### 4.11 Tokens ID e NUM

O livro explica (Seção 4.3, p. 77) que a estrutura léxica (identificadores, constantes,
palavras-chave) é descrita por expressões regulares, e a gramática trabalha sobre os
*tokens*. Por isso, como no Exemplo 4.11 (p. 80), identificadores e números aparecem na
gramática como os *tokens* `ID` e `NUM`, com a seguinte forma:

```
ID       ::= <letra> { <letra> | <digito> | "_" }
NUM      ::= <digito> { <digito> }
<letra>  ::= a | ... | z | A | ... | Z
<digito> ::= 0 | 1 | ... | 9
```

- Identificadores: `x`, `soma_total`, `a1`. As palavras reservadas (`program var
  integer boolean procedure function begin end if then else while do return break
  continue print true false`) não podem ser usadas como identificador.
- Números: `0`, `42`.
- Comentários ficam entre `{` e `}` e são ignorados.

---

## 5. Por que a gramática é LL(1)

O livro define (p. 85): uma gramática é **LL(1)** quando a sua tabela sintática
preditiva (Algoritmo 4.4) não tem entradas multiplamente definidas. O primeiro "L" é a
leitura da esquerda para a direita, o segundo "L" é a derivação mais à esquerda, e o
"1" é o único símbolo de *lookahead* usado em cada decisão. Gramáticas LL(1) podem ser
analisadas por um analisador **preditivo** de descendência recursiva, sem retrocesso
(p. 81).

O livro também observa que **nenhuma gramática ambígua ou recursiva à esquerda pode
ser LL(1)** (p. 85). Por isso, a construção seguiu três passos: eliminar a recursão à
esquerda (5.1), fatorar à esquerda (5.2), eliminar a ambiguidade do `if` (5.3). Por
fim, as condições LL(1) foram conferidas com PRIMEIRO e SEGUINTE (5.4).

### 5.1 Sem recursão à esquerda

Uma gramática é recursiva à esquerda se existe `A ⇒ Aα`. Um analisador de descendência
recursiva entra em **laço infinito** nela: para expandir `A`, chama `A` de novo sem
consumir nenhum símbolo da entrada (p. 81).

A forma "natural" das expressões tem esse problema (gramática 4.10 do livro):

```
<expressao_simples> ::= <expressao_simples> "+" <termo> | <termo>     { recursiva à esquerda }
```

Aplicamos a transformação do livro (p. 79): `A → Aα | β` vira `A → βA'` e
`A' → αA' | ε`:

```
<expressao_simples>       ::= <termo> <resto_expressao_simples>
<resto_expressao_simples> ::= "+" <termo> <resto_expressao_simples> | ε
```

O mesmo foi feito em `<termo>`/`<resto_termo>` e em todas as listas
(`mais_identificadores`, `mais_parametros`, `mais_argumentos`, `mais_declaracoes`,
`lista_comandos`). Nenhuma produção da gramática começa, direta ou indiretamente, pelo
próprio não-terminal.

### 5.2 Fatorada à esquerda

Pelo Algoritmo 4.2 (p. 80), se duas alternativas têm prefixo comum
(`A → αβ1 | αβ2`), elas viram `A → αA'` e `A' → β1 | β2`. Pontos onde isso foi feito:

| Situação | Antes (não LL(1)) | Depois |
|---|---|---|
| Atribuição × chamada de procedimento | `ID ":=" ...` \| `ID "(" ...` | `ID <resto_comando_identificador>` |
| Variável × chamada de função | `ID` \| `ID "(" ...` | `ID <resto_fator>` |
| `if` com e sem `else` | `"if" ...` \| `"if" ... "else" ...` | `"if" ... <parte_senao>` |

### 5.3 Sem ambiguidade

A única fonte de ambiguidade comum nesse tipo de linguagem é o `if-then-else` (p. 78).
Ela foi eliminada exigindo `begin ... end` no corpo do `if` e do `else` (seção 4.6). As
expressões não são ambíguas porque a precedência está codificada nos níveis
`<expressao>` → `<expressao_simples>` → `<termo>` → `<fator>` (p. 77, Exemplo 4.6).

### 5.4 Conferência com PRIMEIRO e SEGUINTE

Definições do livro (p. 84):

- **PRIMEIRO(α)**: conjunto dos terminais que começam as cadeias derivadas de α (inclui
  ε se α ⇒ ε).
- **SEGUINTE(A)**: conjunto dos terminais que podem aparecer imediatamente à direita
  de A em alguma forma sentencial (inclui `$`, o fim da entrada, se A pode ser o último
  símbolo).

Condições do livro para LL(1) (p. 85). Para cada par de produções distintas
`A → α | β`:

1. α e β não derivam cadeias começando pelo mesmo terminal;
2. no máximo um dos dois, α ou β, deriva a cadeia vazia;
3. se β ⇒ ε, então α não deriva cadeia começando por um terminal em SEGUINTE(A).

As condições 1 e 2 se verificam direto nas produções. Todas as alternativas de cada
não-terminal começam com terminais diferentes, e nenhum não-terminal tem duas
alternativas que geram ε. A condição 3 é a que exige cálculo: vale para os
não-terminais que têm alternativa ε, pois neles o analisador precisa saber **quando
parar**. A tabela abaixo mostra que, em todos eles, PRIMEIRO da alternativa não vazia
e SEGUINTE do não-terminal não têm nenhum terminal em comum:

| Não-terminal | PRIMEIRO da alternativa não vazia | SEGUINTE (usa ε) |
|---|---|---|
| `<secao_variaveis>` | { `var` } | { `begin`, `function`, `procedure` } |
| `<mais_declaracoes>` | { `ID` } | { `begin`, `function`, `procedure` } |
| `<mais_identificadores>` | { `,` } | { `:` } |
| `<secao_subrotinas>` | { `function`, `procedure` } | { `begin` } |
| `<lista_parametros>` | { `ID` } | { `)` } |
| `<mais_parametros>` | { `,` } | { `)` } |
| `<lista_comandos>` | { `ID`, `begin`, `break`, `continue`, `if`, `print`, `return`, `while` } | { `end` } |
| `<lista_argumentos>` | { `(`, `-`, `ID`, `NUM`, `false`, `true` } | { `)` } |
| `<mais_argumentos>` | { `,` } | { `)` } |
| `<parte_senao>` | { `else` } | { `ID`, `begin`, `break`, `continue`, `end`, `if`, `print`, `return`, `while` } |
| `<resto_expressao>` | { `!=`, `<`, `<=`, `==`, `>`, `>=` } | { `)`, `,`, `;`, `do`, `then` } |
| `<resto_expressao_simples>` | { `+`, `-` } | { `!=`, `)`, `,`, `;`, `<`, `<=`, `==`, `>`, `>=`, `do`, `then` } |
| `<resto_termo>` | { `*`, `/` } | { `!=`, `)`, `+`, `,`, `-`, `;`, `<`, `<=`, `==`, `>`, `>=`, `do`, `then` } |
| `<resto_fator>` | { `(` } | { `!=`, `)`, `*`, `+`, `,`, `-`, `/`, `;`, `<`, `<=`, `==`, `>`, `>=`, `do`, `then` } |

Leitura de uma linha: em `<mais_identificadores>`, se o próximo *token* for `,`, o
analisador usa `"," ID <mais_identificadores>`; se for `:`, usa ε. Como `,` ≠ `:`, a
decisão é única. Na tabela do Algoritmo 4.4, isso significa que a linha de
`<mais_identificadores>` tem, no máximo, uma produção em cada coluna.

Repare na linha de `<parte_senao>`: `else` **não** está em SEGUINTE. É justamente o
contrário do Exemplo 4.19 do livro, em que `e` (else) está em SEGUINTE(S') e causa a
entrada dupla na tabela.

---

## 6. Como cada requisito da atividade é atendido

| # | Requisito | Produções | Exemplo |
|---|---|---|---|
| 1 | Variáveis inteiro e booleano | `<secao_variaveis>`, `<tipo>` | `var x: integer; ok: boolean;` |
| 2 | Procedimentos e funções, sem e com parâmetros | `<declaracao_procedimento>`, `<declaracao_funcao>`, `<parametros_formais>` | `function f(a: integer): integer;` |
| 3 | Atribuição | `<resto_comando_identificador> ::= ":=" <expressao>` | `x := 1;` |
| 4 | Chamada de procedimentos e funções | `<argumentos>` em comando e em `<resto_fator>` | `p(x);` `y := f(2);` |
| 5 | if / else | `<comando_condicional>`, `<parte_senao>` | `if ... then ... else ...` |
| 6 | while | `<comando_enquanto>` | `while x > 0 do ...` |
| 7 | Retorno de valor | `<comando_retorno>` | `return x * 2;` |
| 8 | break e continue | `<comando_desvio>` | `break;` `continue;` |
| 9 | Impressão de constante e variável | `<comando_escrita>` | `print(10);` `print(x);` |
| 10 | `+ - * /` | `<operador_aditivo>`, `<operador_multiplicativo>` | `a + b * c` |
| 11 | `== != > >= < <=` | `<operador_relacional>` | `x >= 0` |

---

## Referência

AHO, Alfred V.; SETHI, Ravi; ULLMAN, Jeffrey D. *Compiladores: Princípios, Técnicas e
Ferramentas*. Rio de Janeiro: LTC. Capítulo 2 (Seção 2.2) e Capítulo 4 (Seções 4.3 e 4.4).
