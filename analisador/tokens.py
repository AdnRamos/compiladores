"""
tokens.py
=========
Definição dos TOKENS da linguagem: o "vocabulário" que o analisador léxico
entrega ao analisador sintático.

Decisão: cada palavra reservada e cada símbolo tem o SEU PRÓPRIO tipo de token
(em vez de um tipo genérico "PALAVRA_RESERVADA" ou "OPERADOR"). Assim, cada
terminal da gramática (gramatica/gramatica.bnf) corresponde a exatamente um
tipo de token, e o analisador sintático compara tipos diretamente, como nas
produções. Os únicos tokens que carregam um valor variável são ID e NUM
(livro, Seção 3.1: o token é a classe; o lexema é o texto lido).
"""

from dataclasses import dataclass
from enum import Enum


class TipoToken(Enum):
    """Tipos de token. O valor de cada membro é o texto do terminal na
    gramática, usado nas mensagens de erro (ex.: "esperado ':='")."""

    # --- Tokens com lexema variável -------------------------------------
    ID = "identificador"
    NUM = "número"

    # --- Palavras reservadas (gramática, seções 1 a 5) -----------------
    PROGRAM = "program"
    VAR = "var"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    PROCEDURE = "procedure"
    FUNCTION = "function"
    BEGIN = "begin"
    END = "end"
    IF = "if"
    THEN = "then"
    ELSE = "else"
    WHILE = "while"
    DO = "do"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"
    PRINT = "print"
    TRUE = "true"
    FALSE = "false"

    # --- Símbolos com 2 caracteres -------------------------------------
    ATRIBUICAO = ":="
    IGUAL = "=="
    DIFERENTE = "!="
    MAIOR_IGUAL = ">="
    MENOR_IGUAL = "<="

    # --- Símbolos com 1 caractere --------------------------------------
    MAIOR = ">"
    MENOR = "<"
    MAIS = "+"
    MENOS = "-"
    VEZES = "*"
    DIVIDIDO = "/"
    ABRE_PAR = "("
    FECHA_PAR = ")"
    VIRGULA = ","
    PONTO_VIRGULA = ";"
    DOIS_PONTOS = ":"
    PONTO = "."

    # --- Fim da entrada -----------------------------------------------
    # Corresponde ao "$" do livro (Seção 4.4): marca que o texto acabou.
    EOF = "fim do arquivo"


# Tabela de palavras reservadas.
# Decisão (livro, Seção 3.4): o léxico lê palavras-chave e identificadores
# com o MESMO procedimento (letra seguida de letras/dígitos/_) e, ao final,
# consulta esta tabela. Se o lexema estiver aqui, é palavra reservada; senão,
# é ID. Isso evita escrever um autômato separado para cada palavra-chave.
PALAVRAS_RESERVADAS = {
    "program": TipoToken.PROGRAM,
    "var": TipoToken.VAR,
    "integer": TipoToken.INTEGER,
    "boolean": TipoToken.BOOLEAN,
    "procedure": TipoToken.PROCEDURE,
    "function": TipoToken.FUNCTION,
    "begin": TipoToken.BEGIN,
    "end": TipoToken.END,
    "if": TipoToken.IF,
    "then": TipoToken.THEN,
    "else": TipoToken.ELSE,
    "while": TipoToken.WHILE,
    "do": TipoToken.DO,
    "return": TipoToken.RETURN,
    "break": TipoToken.BREAK,
    "continue": TipoToken.CONTINUE,
    "print": TipoToken.PRINT,
    "true": TipoToken.TRUE,
    "false": TipoToken.FALSE,
}

# Símbolos de 2 caracteres. São testados ANTES dos de 1 caractere para
# garantir a regra do "maior lexema possível" (ver lexico.py).
SIMBOLOS_DUPLOS = {
    ":=": TipoToken.ATRIBUICAO,
    "==": TipoToken.IGUAL,
    "!=": TipoToken.DIFERENTE,
    ">=": TipoToken.MAIOR_IGUAL,
    "<=": TipoToken.MENOR_IGUAL,
}

SIMBOLOS_SIMPLES = {
    ">": TipoToken.MAIOR,
    "<": TipoToken.MENOR,
    "+": TipoToken.MAIS,
    "-": TipoToken.MENOS,
    "*": TipoToken.VEZES,
    "/": TipoToken.DIVIDIDO,
    "(": TipoToken.ABRE_PAR,
    ")": TipoToken.FECHA_PAR,
    ",": TipoToken.VIRGULA,
    ";": TipoToken.PONTO_VIRGULA,
    ":": TipoToken.DOIS_PONTOS,
    ".": TipoToken.PONTO,
}


@dataclass
class Token:
    """Um token reconhecido no código-fonte.

    tipo    : classe do token (TipoToken)
    lexema  : texto exato lido do código (ex.: "soma", "42", ":=")
    linha   : linha onde o token começa (a partir de 1)
    coluna  : coluna onde o token começa (a partir de 1)

    Linha e coluna existem só para as mensagens de erro apontarem o local
    exato do problema.
    """

    tipo: TipoToken
    lexema: str
    linha: int
    coluna: int

    def __str__(self):
        return f"{self.linha:>4}:{self.coluna:<4} {self.tipo.name:<14} {self.lexema}"
