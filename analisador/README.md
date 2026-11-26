# Analisadores Léxico e Sintático

Implementação, em Python 3 (sem bibliotecas externas), do analisador léxico e do
analisador sintático para a gramática LL(1) da dupla (`../gramatica/gramatica.bnf`).
Cada decisão está explicada nos comentários do próprio código.

## Como executar

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

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `tokens.py` | Tipos de token, tabela de palavras reservadas e tabela de símbolos |
| `erros.py` | Exceções `ErroLexico` e `ErroSintatico` (com linha e coluna) |
| `lexico.py` | **Analisador léxico**: transforma o texto em tokens |
| `sintatico.py` | **Analisador sintático** descendente recursivo preditivo |
| `main.py` | Programa principal (lê o arquivo e chama os analisadores) |
| `testes.py` | 50 testes: um programa aceito para cada requisito, erros léxicos, erros sintáticos e os exemplos de `../gramatica/exemplos` |

## Como os dois analisadores trabalham juntos

```
código-fonte ──► AnalisadorLexico ──(um token por vez)──► AnalisadorSintatico ──► aceito / erro
                  proximo_token()                          um método por não-terminal
```

O sintático pede um token de cada vez ao léxico (`proximo_token()`), como na Fig. 3.1
do livro. O token atual é o **lookahead**: o único token que o sintático olha para
decidir o que fazer.

## Resumo das decisões

**Analisador léxico (`lexico.py`)**

- Identificadores e palavras reservadas são lidos da mesma forma (letra seguida de
  letras, dígitos ou `_`). Depois, o lexema é procurado na tabela de palavras
  reservadas (livro, Seção 3.4).
- **Maior lexema possível:** `:=`, `==`, `!=`, `>=` e `<=` viram um token só, e
  `whilex` é um identificador, não `while` + `x`.
- **Maiúsculas e minúsculas são diferentes:** `begin` é palavra reservada, mas
  `Begin` é identificador.
- Comentários `{ ... }` e espaços em branco são descartados. Comentários não podem
  ser aninhados.
- **Erros léxicos:** caractere fora da linguagem, `=` ou `!` sozinhos, número colado
  em letra (`12abc`), identificador começando com `_`, comentário não fechado e `}`
  sem `{`.

**Analisador sintático (`sintatico.py`)**

- **Uma função para cada não-terminal** da gramática. A produção está copiada no
  comentário de cada método, então o código pode ser lido lado a lado com
  `gramatica.bnf`.
- **1 token de lookahead e nenhum retrocesso.** Isso só é possível porque a gramática
  é LL(1): sem recursão à esquerda, fatorada à esquerda e sem ambiguidade.
- **Alternativas ε** são decididas com PRIMEIRO e SEGUINTE, como na tabela sintática
  do Algoritmo 4.4 do livro:
  - token em PRIMEIRO → segue a alternativa;
  - token em SEGUINTE → usa ε;
  - qualquer outro token → erro, listando o que era esperado.
- Depois do `.` final, a entrada tem que acabar.
- **O que não é verificado aqui, porque é análise semântica:** variável declarada
  antes do uso, tipos compatíveis, número de argumentos igual ao de parâmetros,
  `return` só dentro de função, e `break`/`continue` só dentro de `while`.

## Verificação

Além de `testes.py`, o analisador foi comparado com um analisador de tabela LL(1)
gerado automaticamente a partir de `gramatica.bnf`. Foram 3000 programas, criados
alterando aleatoriamente o `valido.txt`, e os dois aceitaram e rejeitaram exatamente
os mesmos programas.
