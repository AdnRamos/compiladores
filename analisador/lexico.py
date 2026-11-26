"""
lexico.py
=========
ANALISADOR LÉXICO (scanner).

Função: ler o código-fonte caractere por caractere e agrupar os caracteres em
TOKENS (identificadores, números, palavras reservadas e símbolos), descartando
espaços em branco e comentários. (Livro, Seção 3.1.)

Como ele conversa com o analisador sintático
--------------------------------------------
Decisão: o léxico é chamado SOB DEMANDA. O sintático pede "o próximo token"
pelo método proximo_token() sempre que precisa, como na Fig. 3.1 do livro.
Assim o texto é percorrido uma única vez e não é preciso guardar a lista
inteira de tokens. (O método tokenizar() existe só para listar os tokens na
tela, útil para depuração e para a apresentação.)

Regras léxicas implementadas (gramatica.bnf, seção 6)
-----------------------------------------------------
    ID       = letra ( letra | dígito | "_" )*
    NUM      = dígito dígito*
    palavras reservadas: program var integer boolean procedure function begin
                         end if then else while do return break continue
                         print true false
    símbolos: :=  ==  !=  >=  <=  >  <  +  -  *  /  (  )  ,  ;  :  .
    comentários: { ... }   (descartados)
    espaços em branco: espaço, tabulação, \\r, \\n   (descartados)

Decisões principais (detalhadas nos comentários de cada método)
---------------------------------------------------------------
1. MAIOR LEXEMA POSSÍVEL: em ":=" o léxico gera UM token ATRIBUICAO, e não
   ":" seguido de "="; o mesmo vale para "==", "!=", ">=", "<=".
2. PALAVRAS RESERVADAS: lidas como identificadores e depois consultadas numa
   tabela (tokens.PALAVRAS_RESERVADAS).
3. DIFERENCIAÇÃO DE MAIÚSCULAS/MINÚSCULAS: a linguagem é case-sensitive.
   "begin" é palavra reservada; "Begin" ou "BEGIN" são identificadores.
4. ERROS LÉXICOS: o léxico para e informa linha/coluna quando encontra:
   - caractere que não pertence à linguagem (ex.: "@", "#", "ç", "_x");
   - "=" ou "!" sozinhos (só existem "==", ":=" e "!=");
   - número colado em letra (ex.: "12abc");
   - comentário aberto com "{" e nunca fechado, ou "}" sem "{".
"""

from erros import ErroLexico
from tokens import (PALAVRAS_RESERVADAS, SIMBOLOS_DUPLOS, SIMBOLOS_SIMPLES,
                    Token, TipoToken)


def eh_letra(c):
    """Só letras ASCII (a-z, A-Z), como em gramatica.bnf.
    Decisão: str.isalpha() aceitaria "ç" e "á"; por isso a checagem é manual."""
    return ("a" <= c <= "z") or ("A" <= c <= "Z")


def eh_digito(c):
    """Só dígitos 0-9 (str.isdigit() aceitaria outros, como "²")."""
    return "0" <= c <= "9"


class AnalisadorLexico:
    def __init__(self, codigo):
        self.codigo = codigo   # texto completo do programa
        self.pos = 0           # índice do próximo caractere a ser lido
        self.linha = 1         # linha do próximo caractere
        self.coluna = 1        # coluna do próximo caractere

    # ------------------------------------------------------------------
    # Funções auxiliares de leitura
    # ------------------------------------------------------------------
    def _atual(self):
        """Caractere atual, sem consumir. Retorna "" no fim do texto."""
        return self.codigo[self.pos] if self.pos < len(self.codigo) else ""

    def _seguinte(self):
        """Caractere depois do atual (1 caractere de lookahead, usado para
        decidir entre ":" e ":=", ">" e ">=" etc.)."""
        p = self.pos + 1
        return self.codigo[p] if p < len(self.codigo) else ""

    def _avancar(self):
        """Consome o caractere atual, atualizando linha e coluna."""
        c = self._atual()
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    # ------------------------------------------------------------------
    # Descartar o que não é token
    # ------------------------------------------------------------------
    def _pular_espacos_e_comentarios(self):
        """Descarta espaços em branco e comentários { ... } antes do próximo
        token. Repete porque pode haver vários seguidos, ex.:  "  { a } { b }  x".

        Decisão: comentários NÃO podem ser aninhados ({ a { b } c } não é
        permitido): o primeiro "}" fecha o comentário. É a regra mais simples
        e a mesma do Pascal.
        """
        while True:
            c = self._atual()
            if c in (" ", "\t", "\r", "\n"):
                self._avancar()
            elif c == "{":
                linha, coluna = self.linha, self.coluna   # para a mensagem de erro
                self._avancar()
                while self._atual() != "}":
                    if self._atual() == "":
                        raise ErroLexico("comentário aberto com '{' e não fechado",
                                         linha, coluna)
                    self._avancar()
                self._avancar()   # consome o "}"
            else:
                return

    # ------------------------------------------------------------------
    # Reconhecimento dos tokens
    # ------------------------------------------------------------------
    def proximo_token(self):
        """Lê e retorna o próximo token do código.

        A decisão sobre QUAL token reconhecer é tomada pelo primeiro caractere
        (como num diagrama de transições do livro, Seção 3.4):
            letra        -> identificador ou palavra reservada
            dígito       -> número
            outro        -> símbolo (ou erro)
            fim do texto -> EOF
        """
        self._pular_espacos_e_comentarios()

        linha, coluna = self.linha, self.coluna   # início do token
        c = self._atual()

        if c == "":
            return Token(TipoToken.EOF, "", linha, coluna)
        if eh_letra(c):
            return self._identificador_ou_reservada(linha, coluna)
        if eh_digito(c):
            return self._numero(linha, coluna)
        return self._simbolo(linha, coluna)

    def _identificador_ou_reservada(self, linha, coluna):
        """ID = letra (letra | dígito | "_")*

        Lê o MAIOR lexema possível: "whilex" é o identificador "whilex", e não
        a palavra "while" seguida de "x". Só depois consulta a tabela de
        palavras reservadas.
        """
        inicio = self.pos
        while eh_letra(self._atual()) or eh_digito(self._atual()) or self._atual() == "_":
            self._avancar()
        lexema = self.codigo[inicio:self.pos]
        tipo = PALAVRAS_RESERVADAS.get(lexema, TipoToken.ID)
        return Token(tipo, lexema, linha, coluna)

    def _numero(self, linha, coluna):
        """NUM = dígito dígito*

        Decisão: só números inteiros (a linguagem só tem o tipo integer).
        Decisão: um número colado em letra ou "_" (ex.: "12abc") é ERRO LÉXICO.
        Sem essa regra, "12abc" viraria NUM(12) e ID(abc), e o erro só
        apareceria no sintático, com uma mensagem menos clara.
        Verificar se o valor cabe num inteiro da máquina NÃO é feito aqui:
        isso é papel da análise semântica.
        """
        inicio = self.pos
        while eh_digito(self._atual()):
            self._avancar()
        if eh_letra(self._atual()) or self._atual() == "_":
            raise ErroLexico("número mal formado: dígitos seguidos de letra "
                             f"('{self.codigo[inicio:self.pos]}{self._atual()}...')",
                             linha, coluna)
        return Token(TipoToken.NUM, self.codigo[inicio:self.pos], linha, coluna)

    def _simbolo(self, linha, coluna):
        """Símbolos e operadores.

        Decisão (maior lexema possível): primeiro tenta os símbolos de 2
        caracteres (":=", "==", "!=", ">=", "<="); só se não casar tenta os
        de 1 caractere. Assim ">=" vira MAIOR_IGUAL, e não MAIOR + "=".
        """
        dois = self._atual() + self._seguinte()
        if dois in SIMBOLOS_DUPLOS:
            self._avancar()
            self._avancar()
            return Token(SIMBOLOS_DUPLOS[dois], dois, linha, coluna)

        c = self._atual()
        if c in SIMBOLOS_SIMPLES:
            self._avancar()
            return Token(SIMBOLOS_SIMPLES[c], c, linha, coluna)

        # Nada casou: erro léxico. Mensagens específicas para os erros mais
        # comuns, para o programador entender o que fazer.
        if c == "=":
            msg = "'=' sozinho não existe: use ':=' para atribuição ou '==' para comparação"
        elif c == "!":
            msg = "'!' sozinho não existe: use '!=' para 'diferente'"
        elif c == "}":
            msg = "'}' sem um '{' correspondente"
        elif c == "_":
            msg = "identificador não pode começar com '_'"
        else:
            msg = f"caractere inválido '{c}'"
        raise ErroLexico(msg, linha, coluna)

    # ------------------------------------------------------------------
    def tokenizar(self):
        """Lê o código inteiro e devolve a lista de tokens (incluindo o EOF).
        Usado só para exibir os tokens; o sintático usa proximo_token()."""
        lista = []
        while True:
            token = self.proximo_token()
            lista.append(token)
            if token.tipo == TipoToken.EOF:
                return lista
