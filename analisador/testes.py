"""
testes.py
=========
Testes automáticos dos analisadores léxico e sintático.

Uso (dentro da pasta analisador):
    python testes.py

Cada caso é um pequeno programa e o resultado esperado:
    None              -> o programa deve ser ACEITO
    ("lexico", L)     -> deve dar ERRO LÉXICO na linha L
    ("sintatico", L)  -> deve dar ERRO SINTÁTICO na linha L
Além disso, todos os arquivos de ../gramatica/exemplos são testados
(valido.txt deve ser aceito; os de invalidos/ devem ser rejeitados).
"""

import glob
import os
import sys

from erros import ErroLexico, ErroSintatico
from lexico import AnalisadorLexico
from sintatico import AnalisadorSintatico
from tokens import TipoToken as T


def analisar(codigo):
    """Retorna None se aceito, ou ("lexico"/"sintatico", linha) se houve erro."""
    try:
        AnalisadorSintatico(AnalisadorLexico(codigo)).analisar()
        return None
    except ErroLexico as e:
        return ("lexico", e.linha)
    except ErroSintatico as e:
        return ("sintatico", e.linha)


def prog(corpo, declaracoes=""):
    """Monta um programa mínimo em volta de um trecho, para os testes ficarem curtos.
    O corpo começa na linha 4."""
    return f"program t;\nvar x, y: integer; b: boolean;\n{declaracoes}begin\n{corpo}\nend."


CASOS = [
    # ---------------- programas aceitos (um por requisito) ----------------
    ("programa mínimo, sem variáveis", "program t; begin end.", None),
    ("1. variáveis integer e boolean", prog("x := 1;"), None),
    ("2. procedimento sem parâmetros", prog("p();", "procedure p(); begin end;\n"), None),
    ("2. função com parâmetros e variável local",
     prog("x := f(1, true);",
          "function f(a: integer, c: boolean): integer; var r: integer; begin return a; end;\n"),
     None),
    ("3. atribuição", prog("x := y;"), None),
    ("4. chamada de função dentro de expressão", prog("x := f() + g(x, y * 2);"), None),
    ("5. if sem else", prog("if x > 0 then begin x := 1; end"), None),
    ("5. if com else", prog("if x > 0 then begin x := 1; end else begin x := 2; end"), None),
    ("5. else if", prog("if x > 0 then begin end else if x < 0 then begin end else begin end"), None),
    ("6. while", prog("while x >= 0 do begin x := x - 1; end"), None),
    ("7. return", prog("return x * 2;"), None),
    ("8. break e continue", prog("while b do begin break; continue; end"), None),
    ("9. print de constante e variável", prog("print(10); print(true); print(x);"), None),
    ("10. aritméticas com precedência e parênteses", prog("x := (x + y) * 2 - y / 3;"), None),
    ("10. menos unário", prog("x := -x + -(-y);"), None),
    ("11. todos os relacionais",
     prog("b := x == y; b := x != y; b := x > y; b := x >= y; b := x < y; b := x <= y;"), None),
    ("comparação entre booleanos com parênteses", prog("b := (x < y) == b;"), None),
    ("blocos aninhados e vazios", prog("begin begin end end"), None),
    ("comentários em várias linhas", prog("{ comentário\n em duas linhas } x := 1; { fim }"), None),
    ("'Begin' com maiúscula é identificador",
     "program t;\nvar Begin: integer;\nbegin\nBegin := 1;\nend.", None),

    # ---------------- erros léxicos ----------------
    ("'=' sozinho", prog("x = 1;"), ("lexico", 4)),
    ("'!' sozinho", prog("b := !b;"), ("lexico", 4)),
    ("caractere inválido", prog("x := 1 @ 2;"), ("lexico", 4)),
    ("letra acentuada fora de comentário", prog("ação := 1;"), ("lexico", 4)),
    ("número colado em letra", prog("x := 12abc;"), ("lexico", 4)),
    ("identificador começando com _", prog("_x := 1;"), ("lexico", 4)),
    ("comentário não fechado", prog("{ sem fim\n x := 1;"), ("lexico", 4)),
    ("'}' sem '{'", prog("x := 1; }"), ("lexico", 4)),

    # ---------------- erros sintáticos ----------------
    ("falta ';' depois de comando simples", prog("x := 1\ny := 2;"), ("sintatico", 5)),
    ("';' depois de end de if", prog("if b then begin end;"), ("sintatico", 4)),
    ("corpo do if sem begin/end", prog("if b then x := 1;"), ("sintatico", 4)),
    ("chamada sem parênteses", prog("p;"), ("sintatico", 4)),
    ("relacional encadeado", prog("b := x < y < 3;"), ("sintatico", 4)),
    ("operador sem operando", prog("x := 1 + ;"), ("sintatico", 4)),
    ("parêntese não fechado", prog("x := (1 + 2;"), ("sintatico", 4)),
    ("palavra reservada como variável", prog("while := 1;"), ("sintatico", 4)),
    ("tipo inexistente", "program t;\nvar x: real;\nbegin end.", ("sintatico", 2)),
    ("variável declarada depois de sub-rotina",
     "program t;\nprocedure p(); begin end;\nvar x: integer;\nbegin end.", ("sintatico", 3)),
    ("função sem tipo de retorno",
     "program t;\nfunction f();\nbegin end;\nbegin end.", ("sintatico", 2)),
    ("lixo depois do '.' final", "program t; begin end.\nx := 1;", ("sintatico", 2)),
    ("programa sem '.' no final", "program t; begin end", ("sintatico", 1)),
    ("else sem if", prog("else begin end"), ("sintatico", 4)),
]


def testar_tokens():
    """Confere a regra do maior lexema e o reconhecimento de palavras reservadas."""
    tipos = [t.tipo for t in AnalisadorLexico("x:=a>=b whilex while 007").tokenizar()]
    esperado = [T.ID, T.ATRIBUICAO, T.ID, T.MAIOR_IGUAL, T.ID, T.ID, T.WHILE, T.NUM, T.EOF]
    return tipos == esperado


def main():
    falhas = 0

    for descricao, codigo, esperado in CASOS:
        obtido = analisar(codigo)
        ok = obtido == esperado
        falhas += not ok
        print(f"[{'OK' if ok else 'FALHOU'}] {descricao}"
              + ("" if ok else f"  (esperado {esperado}, obtido {obtido})"))

    ok = testar_tokens()
    falhas += not ok
    print(f"[{'OK' if ok else 'FALHOU'}] léxico: maior lexema e palavras reservadas")

    # Exemplos da pasta gramatica
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gramatica", "exemplos")
    arquivos = [(os.path.join(pasta, "valido.txt"), True)]
    arquivos += [(a, False) for a in sorted(glob.glob(os.path.join(pasta, "invalidos", "*.txt")))]
    for caminho, deve_aceitar in arquivos:
        if not os.path.exists(caminho):
            continue
        with open(caminho, encoding="utf-8") as f:
            aceito = analisar(f.read()) is None
        ok = aceito == deve_aceitar
        falhas += not ok
        print(f"[{'OK' if ok else 'FALHOU'}] exemplo {os.path.basename(caminho)} "
              f"({'aceito' if aceito else 'rejeitado'})")

    print(f"\n{'Todos os testes passaram.' if falhas == 0 else f'{falhas} teste(s) falharam.'}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
