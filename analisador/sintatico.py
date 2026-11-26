"""
sintatico.py
============
ANALISADOR SINTÁTICO DESCENDENTE RECURSIVO PREDITIVO (parser top-down).

Função: verificar se a sequência de tokens produzida pelo analisador léxico
segue a gramática da linguagem (gramatica/gramatica.bnf).

Como o analisador foi construído (livro, Seção 4.4, "Analisadores Sintáticos
Preditivos" e Seção 2.4)
------------------------------------------------------------------------------
1. UMA FUNÇÃO POR NÃO-TERMINAL. Cada produção <x> da gramática virou um
   método x(). O corpo do método segue o lado direito da produção, da
   esquerda para a direita:
       - terminal       -> self._consumir(TIPO)   (confere e avança)
       - não-terminal   -> chamada do método correspondente
   Por isso o código pode ser lido lado a lado com gramatica.bnf: a produção
   está copiada no comentário de cada método.

2. UM TOKEN DE LOOKAHEAD. O analisador olha sempre só o token atual
   (self.atual) para decidir qual alternativa seguir. Isso só funciona porque
   a gramática é LL(1): sem recursão à esquerda (senão um método chamaria a
   si mesmo sem consumir nada, laço infinito), fatorada à esquerda (senão
   duas alternativas começariam igual) e sem ambiguidade.

3. SEM RETROCESSO (backtracking). Uma vez escolhida a alternativa, o
   analisador nunca volta atrás. Se algo não casar, é erro.

4. ESCOLHA ENTRE ALTERNATIVAS:
   - Alternativas que começam com terminais diferentes: o token atual diz
     qual seguir (ex.: <comando>, <fator>, <tipo>).
   - Alternativa vazia (ε): usa-se os conjuntos PRIMEIRO e SEGUINTE, como na
     tabela sintática do Algoritmo 4.4 do livro:
         token atual em PRIMEIRO(alternativa não vazia) -> segue essa alternativa
         token atual em SEGUINTE(não-terminal)          -> usa ε (não consome nada)
         qualquer outro token                           -> ERRO
     Decisão: conferir o SEGUINTE (em vez de simplesmente "usar ε quando não
     for PRIMEIRO") faz o erro ser detectado no ponto mais cedo possível,
     com a lista exata do que era esperado. Os conjuntos usados estão
     definidos logo abaixo e são os mesmos da tabela da seção 5.4 de
     gramatica/README.md.

5. ERROS: o analisador para no primeiro erro (ver erros.py), mostrando linha,
   coluna, o token encontrado e os tokens que eram esperados ali.

6. RASTREAMENTO: com rastrear=True, cada não-terminal expandido e cada
   terminal consumido é impresso com recuo, mostrando a árvore de derivação
   que o analisador está construindo (útil para entender e apresentar).
"""

from contextlib import contextmanager

from erros import ErroSintatico
from tokens import TipoToken as T

# ============================================================================
# Conjuntos PRIMEIRO e SEGUINTE usados nas decisões (livro, Seção 4.4)
# ============================================================================

# Tokens que podem COMEÇAR uma expressão: PRIMEIRO(<expressao>) = PRIMEIRO(<fator>)
PRIMEIRO_EXPRESSAO = {T.ID, T.NUM, T.TRUE, T.FALSE, T.ABRE_PAR, T.MENOS}

# Tokens que podem COMEÇAR um comando: PRIMEIRO(<comando>)
PRIMEIRO_COMANDO = {T.ID, T.IF, T.WHILE, T.RETURN, T.BREAK, T.CONTINUE,
                    T.PRINT, T.BEGIN}

OPERADORES_RELACIONAIS = {T.IGUAL, T.DIFERENTE, T.MAIOR, T.MAIOR_IGUAL,
                          T.MENOR, T.MENOR_IGUAL}
OPERADORES_ADITIVOS = {T.MAIS, T.MENOS}
OPERADORES_MULTIPLICATIVOS = {T.VEZES, T.DIVIDIDO}

# SEGUINTE dos não-terminais que têm alternativa ε (tabela do README, seção 5.4)
SEGUINTE_SECAO_VARIAVEIS = {T.BEGIN, T.FUNCTION, T.PROCEDURE}
SEGUINTE_MAIS_DECLARACOES = {T.BEGIN, T.FUNCTION, T.PROCEDURE}
SEGUINTE_MAIS_IDENTIFICADORES = {T.DOIS_PONTOS}
SEGUINTE_SECAO_SUBROTINAS = {T.BEGIN}
SEGUINTE_LISTA_PARAMETROS = {T.FECHA_PAR}
SEGUINTE_MAIS_PARAMETROS = {T.FECHA_PAR}
SEGUINTE_LISTA_COMANDOS = {T.END}
SEGUINTE_LISTA_ARGUMENTOS = {T.FECHA_PAR}
SEGUINTE_MAIS_ARGUMENTOS = {T.FECHA_PAR}
SEGUINTE_PARTE_SENAO = PRIMEIRO_COMANDO | {T.END}
# O que pode vir depois de uma expressão inteira:
SEGUINTE_RESTO_EXPRESSAO = {T.FECHA_PAR, T.VIRGULA, T.PONTO_VIRGULA, T.DO, T.THEN}
# Depois de uma expressão simples pode vir também um operador relacional...
SEGUINTE_RESTO_EXPRESSAO_SIMPLES = SEGUINTE_RESTO_EXPRESSAO | OPERADORES_RELACIONAIS
# ...depois de um termo, também um operador aditivo...
SEGUINTE_RESTO_TERMO = SEGUINTE_RESTO_EXPRESSAO_SIMPLES | OPERADORES_ADITIVOS
# ...e depois de um fator, também um operador multiplicativo.
SEGUINTE_RESTO_FATOR = SEGUINTE_RESTO_TERMO | OPERADORES_MULTIPLICATIVOS


def _descrever(tipos):
    """Transforma um conjunto de tipos de token em texto para a mensagem de
    erro, ex.: {T.BEGIN, T.VAR} -> "'begin' ou 'var'"."""
    nomes = sorted(f"'{t.value}'" if t not in (T.ID, T.NUM) else t.value for t in tipos)
    return nomes[0] if len(nomes) == 1 else ", ".join(nomes[:-1]) + " ou " + nomes[-1]


class AnalisadorSintatico:
    def __init__(self, lexico, rastrear=False):
        self.lexico = lexico
        self.rastrear = rastrear
        self.nivel = 0                              # profundidade (recuo do rastreamento)
        self.atual = self.lexico.proximo_token()    # o token de lookahead

    # ========================================================================
    # Funções auxiliares
    # ========================================================================
    def _log(self, texto):
        if self.rastrear:
            print("  " * self.nivel + texto)

    @contextmanager
    def _regra(self, nao_terminal):
        """Marca a entrada e a saída de um não-terminal (só para o rastreamento).
        Uso:  with self._regra("<programa>"): ..."""
        self._log(nao_terminal)
        self.nivel += 1
        try:
            yield
        finally:
            self.nivel -= 1

    def _consumir(self, tipo):
        """Casa um TERMINAL da produção com o token atual.

        Se o token atual for do tipo esperado, ele é consumido e o léxico é
        chamado para trazer o próximo token (o novo lookahead). Senão, erro.
        É o "reconhecer(t)" do analisador preditivo do livro (Seção 2.4).
        """
        if self.atual.tipo != tipo:
            self._erro({tipo})
        self._log(f'"{self.atual.lexema}"' if self.atual.tipo not in (T.ID, T.NUM)
                  else f"{self.atual.tipo.name}({self.atual.lexema})")
        self.atual = self.lexico.proximo_token()

    def _usa_alternativa(self, primeiro, seguinte):
        """Decide entre a alternativa NÃO vazia e a alternativa ε de uma
        produção  A ::= α | ε  (ver item 4 do cabeçalho).

        Retorna True  -> seguir α        (token atual em PRIMEIRO(α))
                False -> usar ε          (token atual em SEGUINTE(A))
        Qualquer outro token é erro: não está em nenhuma entrada da tabela.
        """
        if self.atual.tipo in primeiro:
            return True
        if self.atual.tipo in seguinte:
            self._log("ε")
            return False
        self._erro(primeiro | seguinte)

    def _erro(self, esperados):
        encontrado = (self.atual.tipo.value if self.atual.tipo == T.EOF
                      else f"'{self.atual.lexema}'")
        raise ErroSintatico(f"esperado {_descrever(esperados)}, encontrado {encontrado}",
                            self.atual.linha, self.atual.coluna)

    # ========================================================================
    # Ponto de entrada
    # ========================================================================
    def analisar(self):
        """Analisa o programa inteiro.

        Depois de reconhecer <programa> (o símbolo de partida), o próximo token
        TEM que ser o fim do arquivo (o "$" do livro). Isso impede que haja
        lixo depois do "." final, ex.: "end. x := 1;".
        """
        self.programa()
        if self.atual.tipo != T.EOF:
            self._erro({T.EOF})

    # ========================================================================
    # 1. ESTRUTURA DO PROGRAMA
    # ========================================================================
    def programa(self):
        # <programa> ::= "program" ID ";" <bloco> "."
        with self._regra("<programa>"):
            self._consumir(T.PROGRAM)
            self._consumir(T.ID)
            self._consumir(T.PONTO_VIRGULA)
            self.bloco()
            self._consumir(T.PONTO)

    def bloco(self):
        # <bloco> ::= <secao_variaveis> <secao_subrotinas> <comando_composto>
        # A ordem é fixa: variáveis, depois sub-rotinas, depois o corpo.
        with self._regra("<bloco>"):
            self.secao_variaveis()
            self.secao_subrotinas()
            self.comando_composto()

    # ========================================================================
    # 2. DECLARAÇÃO DE VARIÁVEIS (inteiro e booleano)
    # ========================================================================
    def secao_variaveis(self):
        # <secao_variaveis> ::= "var" <declaracao_variaveis> ";" <mais_declaracoes>
        #                     | ε
        # Decisão: com "var" a seção existe; com begin/procedure/function não existe.
        with self._regra("<secao_variaveis>"):
            if self._usa_alternativa({T.VAR}, SEGUINTE_SECAO_VARIAVEIS):
                self._consumir(T.VAR)
                self.declaracao_variaveis()
                self._consumir(T.PONTO_VIRGULA)
                self.mais_declaracoes()

    def mais_declaracoes(self):
        # <mais_declaracoes> ::= <declaracao_variaveis> ";" <mais_declaracoes>
        #                      | ε
        # Decisão: um ID inicia outra declaração (ex.: "achou: boolean;").
        # A recursão é À DIREITA (a chamada está no fim), por isso não há laço
        # infinito: cada chamada consome pelo menos um ID antes de se repetir.
        with self._regra("<mais_declaracoes>"):
            if self._usa_alternativa({T.ID}, SEGUINTE_MAIS_DECLARACOES):
                self.declaracao_variaveis()
                self._consumir(T.PONTO_VIRGULA)
                self.mais_declaracoes()

    def declaracao_variaveis(self):
        # <declaracao_variaveis> ::= <lista_identificadores> ":" <tipo>
        with self._regra("<declaracao_variaveis>"):
            self.lista_identificadores()
            self._consumir(T.DOIS_PONTOS)
            self.tipo()

    def lista_identificadores(self):
        # <lista_identificadores> ::= ID <mais_identificadores>
        with self._regra("<lista_identificadores>"):
            self._consumir(T.ID)
            self.mais_identificadores()

    def mais_identificadores(self):
        # <mais_identificadores> ::= "," ID <mais_identificadores>
        #                          | ε
        # Decisão: "," -> vem outro nome; ":" -> a lista acabou.
        with self._regra("<mais_identificadores>"):
            if self._usa_alternativa({T.VIRGULA}, SEGUINTE_MAIS_IDENTIFICADORES):
                self._consumir(T.VIRGULA)
                self._consumir(T.ID)
                self.mais_identificadores()

    def tipo(self):
        # <tipo> ::= "integer" | "boolean"
        with self._regra("<tipo>"):
            if self.atual.tipo == T.INTEGER:
                self._consumir(T.INTEGER)
            elif self.atual.tipo == T.BOOLEAN:
                self._consumir(T.BOOLEAN)
            else:
                self._erro({T.INTEGER, T.BOOLEAN})

    # ========================================================================
    # 3. DECLARAÇÃO DE PROCEDIMENTOS E FUNÇÕES (sem e com parâmetros)
    # ========================================================================
    def secao_subrotinas(self):
        # <secao_subrotinas> ::= <declaracao_subrotina> <secao_subrotinas>
        #                      | ε
        # Decisão: "procedure"/"function" -> mais uma sub-rotina; "begin" -> acabou.
        with self._regra("<secao_subrotinas>"):
            if self._usa_alternativa({T.PROCEDURE, T.FUNCTION}, SEGUINTE_SECAO_SUBROTINAS):
                self.declaracao_subrotina()
                self.secao_subrotinas()

    def declaracao_subrotina(self):
        # <declaracao_subrotina> ::= <declaracao_procedimento>
        #                          | <declaracao_funcao>
        # Decisão: a palavra reservada diz qual é.
        with self._regra("<declaracao_subrotina>"):
            if self.atual.tipo == T.PROCEDURE:
                self.declaracao_procedimento()
            elif self.atual.tipo == T.FUNCTION:
                self.declaracao_funcao()
            else:
                self._erro({T.PROCEDURE, T.FUNCTION})

    def declaracao_procedimento(self):
        # <declaracao_procedimento> ::= "procedure" ID <parametros_formais> ";"
        #                               <corpo_subrotina> ";"
        # Procedimento não tem tipo de retorno.
        with self._regra("<declaracao_procedimento>"):
            self._consumir(T.PROCEDURE)
            self._consumir(T.ID)
            self.parametros_formais()
            self._consumir(T.PONTO_VIRGULA)
            self.corpo_subrotina()
            self._consumir(T.PONTO_VIRGULA)

    def declaracao_funcao(self):
        # <declaracao_funcao> ::= "function" ID <parametros_formais> ":" <tipo> ";"
        #                         <corpo_subrotina> ";"
        # Função declara o tipo do valor que retorna, depois do ":".
        with self._regra("<declaracao_funcao>"):
            self._consumir(T.FUNCTION)
            self._consumir(T.ID)
            self.parametros_formais()
            self._consumir(T.DOIS_PONTOS)
            self.tipo()
            self._consumir(T.PONTO_VIRGULA)
            self.corpo_subrotina()
            self._consumir(T.PONTO_VIRGULA)

    def corpo_subrotina(self):
        # <corpo_subrotina> ::= <secao_variaveis> <comando_composto>
        # Decisão da gramática: sub-rotina tem variáveis locais, mas não pode
        # declarar outras sub-rotinas dentro dela (sem aninhamento).
        with self._regra("<corpo_subrotina>"):
            self.secao_variaveis()
            self.comando_composto()

    def parametros_formais(self):
        # <parametros_formais> ::= "(" <lista_parametros> ")"
        # Os parênteses são obrigatórios mesmo sem parâmetros: "procedure p();"
        with self._regra("<parametros_formais>"):
            self._consumir(T.ABRE_PAR)
            self.lista_parametros()
            self._consumir(T.FECHA_PAR)

    def lista_parametros(self):
        # <lista_parametros> ::= <parametro> <mais_parametros>
        #                      | ε
        # Decisão: ID -> há parâmetros; ")" -> lista vazia (sub-rotina sem parâmetros).
        with self._regra("<lista_parametros>"):
            if self._usa_alternativa({T.ID}, SEGUINTE_LISTA_PARAMETROS):
                self.parametro()
                self.mais_parametros()

    def mais_parametros(self):
        # <mais_parametros> ::= "," <parametro> <mais_parametros>
        #                     | ε
        with self._regra("<mais_parametros>"):
            if self._usa_alternativa({T.VIRGULA}, SEGUINTE_MAIS_PARAMETROS):
                self._consumir(T.VIRGULA)
                self.parametro()
                self.mais_parametros()

    def parametro(self):
        # <parametro> ::= ID ":" <tipo>
        with self._regra("<parametro>"):
            self._consumir(T.ID)
            self._consumir(T.DOIS_PONTOS)
            self.tipo()

    # ========================================================================
    # 4. COMANDOS
    # ========================================================================
    def comando_composto(self):
        # <comando_composto> ::= "begin" <lista_comandos> "end"
        with self._regra("<comando_composto>"):
            self._consumir(T.BEGIN)
            self.lista_comandos()
            self._consumir(T.END)

    def lista_comandos(self):
        # <lista_comandos> ::= <comando> <lista_comandos>
        #                    | ε
        # Decisão: qualquer token que inicia um comando -> mais um comando;
        # "end" -> a lista acabou (um bloco "begin end" vazio é permitido).
        with self._regra("<lista_comandos>"):
            if self._usa_alternativa(PRIMEIRO_COMANDO, SEGUINTE_LISTA_COMANDOS):
                self.comando()
                self.lista_comandos()

    def comando(self):
        # <comando> ::= <comando_identificador> ";"
        #             | <comando_condicional>
        #             | <comando_enquanto>
        #             | <comando_retorno> ";"
        #             | <comando_desvio> ";"
        #             | <comando_escrita> ";"
        #             | <comando_composto>
        #
        # Decisão: cada alternativa começa com um token diferente, então o
        # token atual escolhe sozinho (livro, p. 81-82).
        # Decisão sobre o ";": ele TERMINA os comandos simples (atribuição,
        # chamada, return, break, continue, print). Os comandos que terminam
        # em "end" (if, while, begin...end) não levam ";".
        with self._regra("<comando>"):
            tipo = self.atual.tipo
            if tipo == T.ID:
                self.comando_identificador()
                self._consumir(T.PONTO_VIRGULA)
            elif tipo == T.IF:
                self.comando_condicional()
            elif tipo == T.WHILE:
                self.comando_enquanto()
            elif tipo == T.RETURN:
                self.comando_retorno()
                self._consumir(T.PONTO_VIRGULA)
            elif tipo in (T.BREAK, T.CONTINUE):
                self.comando_desvio()
                self._consumir(T.PONTO_VIRGULA)
            elif tipo == T.PRINT:
                self.comando_escrita()
                self._consumir(T.PONTO_VIRGULA)
            elif tipo == T.BEGIN:
                self.comando_composto()
            else:
                self._erro(PRIMEIRO_COMANDO)

    def comando_identificador(self):
        # <comando_identificador> ::= ID <resto_comando_identificador>
        #
        # Decisão (FATORAÇÃO À ESQUERDA, livro Algoritmo 4.2): atribuição
        # "x := ..." e chamada de procedimento "p(...)" começam ambas com ID.
        # Com 1 token de lookahead não dá para saber qual é; então o ID é lido
        # aqui e a decisão fica para o token seguinte, em
        # <resto_comando_identificador>.
        with self._regra("<comando_identificador>"):
            self._consumir(T.ID)
            self.resto_comando_identificador()

    def resto_comando_identificador(self):
        # <resto_comando_identificador> ::= ":=" <expressao>      (atribuição)
        #                                 | <argumentos>          (chamada)
        with self._regra("<resto_comando_identificador>"):
            if self.atual.tipo == T.ATRIBUICAO:
                self._consumir(T.ATRIBUICAO)
                self.expressao()
            elif self.atual.tipo == T.ABRE_PAR:
                self.argumentos()
            else:
                # Ex.: "ola;" (chamada sem parênteses) ou "x = 1;"
                self._erro({T.ATRIBUICAO, T.ABRE_PAR})

    def argumentos(self):
        # <argumentos> ::= "(" <lista_argumentos> ")"
        # Usado tanto na chamada de procedimento (comando) quanto na chamada
        # de função (dentro de expressões, em <resto_fator>).
        with self._regra("<argumentos>"):
            self._consumir(T.ABRE_PAR)
            self.lista_argumentos()
            self._consumir(T.FECHA_PAR)

    def lista_argumentos(self):
        # <lista_argumentos> ::= <expressao> <mais_argumentos>
        #                      | ε
        # Decisão: um token que inicia expressão -> há argumentos; ")" -> nenhum.
        # Conferir se a quantidade de argumentos bate com a de parâmetros NÃO
        # é feito aqui: é análise semântica (livro, Exemplo 4.12).
        with self._regra("<lista_argumentos>"):
            if self._usa_alternativa(PRIMEIRO_EXPRESSAO, SEGUINTE_LISTA_ARGUMENTOS):
                self.expressao()
                self.mais_argumentos()

    def mais_argumentos(self):
        # <mais_argumentos> ::= "," <expressao> <mais_argumentos>
        #                     | ε
        with self._regra("<mais_argumentos>"):
            if self._usa_alternativa({T.VIRGULA}, SEGUINTE_MAIS_ARGUMENTOS):
                self._consumir(T.VIRGULA)
                self.expressao()
                self.mais_argumentos()

    def comando_condicional(self):
        # <comando_condicional> ::= "if" <expressao> "then" <comando_composto> <parte_senao>
        #
        # Decisão: o corpo do then é um <comando_composto> (begin ... end), e
        # não um <comando> qualquer. Isso elimina a ambiguidade do "else
        # vazio" (livro, p. 78 e Exemplo 4.19): o "else" só pode vir logo
        # depois do "end" que fecha o then, então sempre pertence a este if.
        with self._regra("<comando_condicional>"):
            self._consumir(T.IF)
            self.expressao()
            self._consumir(T.THEN)
            self.comando_composto()
            self.parte_senao()

    def parte_senao(self):
        # <parte_senao> ::= "else" <bloco_senao>
        #                 | ε
        # Decisão: "else" -> tem senão; início de outro comando ou "end" -> não tem.
        # Como "else" NÃO está em SEGUINTE(<parte_senao>), não há conflito.
        with self._regra("<parte_senao>"):
            if self._usa_alternativa({T.ELSE}, SEGUINTE_PARTE_SENAO):
                self._consumir(T.ELSE)
                self.bloco_senao()

    def bloco_senao(self):
        # <bloco_senao> ::= <comando_composto>        (else begin ... end)
        #                 | <comando_condicional>     (else if ...)
        # Decisão: permitir "else if" direto evita um begin/end a mais em
        # cadeias de condições, sem criar ambiguidade (o if de dentro também
        # exige begin ... end).
        with self._regra("<bloco_senao>"):
            if self.atual.tipo == T.BEGIN:
                self.comando_composto()
            elif self.atual.tipo == T.IF:
                self.comando_condicional()
            else:
                self._erro({T.BEGIN, T.IF})

    def comando_enquanto(self):
        # <comando_enquanto> ::= "while" <expressao> "do" <comando_composto>
        # Mesma decisão do if: o corpo é sempre begin ... end.
        with self._regra("<comando_enquanto>"):
            self._consumir(T.WHILE)
            self.expressao()
            self._consumir(T.DO)
            self.comando_composto()

    def comando_retorno(self):
        # <comando_retorno> ::= "return" <expressao>
        # Verificar que "return" só aparece dentro de função é análise
        # semântica; a gramática só garante a forma "return expressão".
        with self._regra("<comando_retorno>"):
            self._consumir(T.RETURN)
            self.expressao()

    def comando_desvio(self):
        # <comando_desvio> ::= "break" | "continue"
        # Verificar que estão dentro de um while também é análise semântica.
        with self._regra("<comando_desvio>"):
            if self.atual.tipo == T.BREAK:
                self._consumir(T.BREAK)
            elif self.atual.tipo == T.CONTINUE:
                self._consumir(T.CONTINUE)
            else:
                self._erro({T.BREAK, T.CONTINUE})

    def comando_escrita(self):
        # <comando_escrita> ::= "print" "(" <expressao> ")"
        # Decisão: o argumento é uma <expressao>, então print aceita tanto
        # constante (print(10), print(true)) quanto variável (print(x)).
        with self._regra("<comando_escrita>"):
            self._consumir(T.PRINT)
            self._consumir(T.ABRE_PAR)
            self.expressao()
            self._consumir(T.FECHA_PAR)

    # ========================================================================
    # 5. EXPRESSÕES
    # ------------------------------------------------------------------------
    # Precedência, da menor para a maior (quanto mais "fundo" na chamada,
    # maior a precedência):
    #     expressao          relacionais  == != > >= < <=
    #     expressao_simples  aditivos     + -
    #     termo              multiplic.   * /
    #     fator              parênteses, - unário, variável, número, chamada
    #
    # Recursão à esquerda eliminada (livro, p. 79): em vez de
    #     <expressao_simples> ::= <expressao_simples> "+" <termo> | <termo>
    # que faria expressao_simples() chamar a si mesma sem consumir nada (laço
    # infinito), usa-se  E -> T E'  e  E' -> + T E' | ε  (Exemplo 4.8 do livro).
    # ========================================================================
    def expressao(self):
        # <expressao> ::= <expressao_simples> <resto_expressao>
        with self._regra("<expressao>"):
            self.expressao_simples()
            self.resto_expressao()

    def resto_expressao(self):
        # <resto_expressao> ::= <operador_relacional> <expressao_simples>
        #                     | ε
        # Decisão: o relacional aparece NO MÁXIMO UMA VEZ (não há chamada
        # recursiva aqui). "a < b < c" é erro: depois de "a < b" o próximo
        # token precisa estar em SEGUINTE, e "<" não está.
        with self._regra("<resto_expressao>"):
            if self._usa_alternativa(OPERADORES_RELACIONAIS, SEGUINTE_RESTO_EXPRESSAO):
                self.operador_relacional()
                self.expressao_simples()

    def operador_relacional(self):
        # <operador_relacional> ::= "==" | "!=" | ">" | ">=" | "<" | "<="
        with self._regra("<operador_relacional>"):
            if self.atual.tipo in OPERADORES_RELACIONAIS:
                self._consumir(self.atual.tipo)
            else:
                self._erro(OPERADORES_RELACIONAIS)

    def expressao_simples(self):
        # <expressao_simples> ::= <termo> <resto_expressao_simples>
        with self._regra("<expressao_simples>"):
            self.termo()
            self.resto_expressao_simples()

    def resto_expressao_simples(self):
        # <resto_expressao_simples> ::= <operador_aditivo> <termo> <resto_expressao_simples>
        #                             | ε
        # (o E' do livro)
        with self._regra("<resto_expressao_simples>"):
            if self._usa_alternativa(OPERADORES_ADITIVOS, SEGUINTE_RESTO_EXPRESSAO_SIMPLES):
                self.operador_aditivo()
                self.termo()
                self.resto_expressao_simples()

    def operador_aditivo(self):
        # <operador_aditivo> ::= "+" | "-"
        with self._regra("<operador_aditivo>"):
            if self.atual.tipo in OPERADORES_ADITIVOS:
                self._consumir(self.atual.tipo)
            else:
                self._erro(OPERADORES_ADITIVOS)

    def termo(self):
        # <termo> ::= <fator> <resto_termo>
        with self._regra("<termo>"):
            self.fator()
            self.resto_termo()

    def resto_termo(self):
        # <resto_termo> ::= <operador_multiplicativo> <fator> <resto_termo>
        #                 | ε
        # (o T' do livro)
        with self._regra("<resto_termo>"):
            if self._usa_alternativa(OPERADORES_MULTIPLICATIVOS, SEGUINTE_RESTO_TERMO):
                self.operador_multiplicativo()
                self.fator()
                self.resto_termo()

    def operador_multiplicativo(self):
        # <operador_multiplicativo> ::= "*" | "/"
        with self._regra("<operador_multiplicativo>"):
            if self.atual.tipo in OPERADORES_MULTIPLICATIVOS:
                self._consumir(self.atual.tipo)
            else:
                self._erro(OPERADORES_MULTIPLICATIVOS)

    def fator(self):
        # <fator> ::= ID <resto_fator>
        #           | NUM
        #           | "true"
        #           | "false"
        #           | "(" <expressao> ")"
        #           | "-" <fator>
        #
        # Decisão: cada alternativa começa com um token diferente.
        # O "-" aqui é o MENOS UNÁRIO (ex.: -x). Não conflita com o "-"
        # binário de <operador_aditivo>: o binário só é procurado DEPOIS de
        # um termo, e o unário só no INÍCIO de um fator.
        with self._regra("<fator>"):
            tipo = self.atual.tipo
            if tipo == T.ID:
                self._consumir(T.ID)
                self.resto_fator()
            elif tipo == T.NUM:
                self._consumir(T.NUM)
            elif tipo == T.TRUE:
                self._consumir(T.TRUE)
            elif tipo == T.FALSE:
                self._consumir(T.FALSE)
            elif tipo == T.ABRE_PAR:
                self._consumir(T.ABRE_PAR)
                self.expressao()
                self._consumir(T.FECHA_PAR)
            elif tipo == T.MENOS:
                self._consumir(T.MENOS)
                self.fator()
            else:
                self._erro(PRIMEIRO_EXPRESSAO)

    def resto_fator(self):
        # <resto_fator> ::= <argumentos>      (chamada de função: f(x))
        #                 | ε                 (variável: x)
        #
        # Decisão (FATORAÇÃO À ESQUERDA): variável e chamada de função começam
        # com ID. O ID já foi lido em fator(); aqui o "(" decide que é chamada.
        with self._regra("<resto_fator>"):
            if self._usa_alternativa({T.ABRE_PAR}, SEGUINTE_RESTO_FATOR):
                self.argumentos()
