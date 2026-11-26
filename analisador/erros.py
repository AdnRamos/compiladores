"""
erros.py
========
Exceções usadas pelos analisadores.

Decisão: os dois analisadores PARAM no primeiro erro encontrado e informam
linha, coluna e o motivo. A atividade pede o reconhecimento da linguagem, e
parar no primeiro erro mantém o código simples e a mensagem sempre correta.
(O livro, Seção 4.4, descreve recuperação de erros na "modalidade do
desespero", que poderia ser acrescentada depois.)
"""


class ErroCompilacao(Exception):
    """Classe base: guarda a posição do erro e monta a mensagem."""

    tipo = "Erro"

    def __init__(self, mensagem, linha, coluna):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        super().__init__(f"{self.tipo} (linha {linha}, coluna {coluna}): {mensagem}")


class ErroLexico(ErroCompilacao):
    """Caractere ou sequência de caracteres que não forma nenhum token."""

    tipo = "Erro léxico"


class ErroSintatico(ErroCompilacao):
    """Sequência de tokens que não segue a gramática."""

    tipo = "Erro sintático"
