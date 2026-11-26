"""
main.py
=======
Programa principal: lê um arquivo-fonte e executa os analisadores.

Uso (dentro da pasta analisador):
    python main.py <arquivo>               analisa o programa
    python main.py <arquivo> --tokens      mostra também a lista de tokens
    python main.py <arquivo> --arvore      mostra também a árvore de derivação

Exemplo:
    python main.py ../gramatica/exemplos/valido.txt --tokens

Saída: "programa aceito" ou a mensagem de erro com linha e coluna.
Código de saída: 0 se o programa foi aceito, 1 se houve erro (útil em scripts).
"""

import sys

from erros import ErroCompilacao
from lexico import AnalisadorLexico
from sintatico import AnalisadorSintatico


def main(argumentos):
    arquivos = [a for a in argumentos if not a.startswith("--")]
    if len(arquivos) != 1:
        print(__doc__)
        return 1
    caminho = arquivos[0]

    try:
        with open(caminho, encoding="utf-8") as f:
            codigo = f.read()
    except OSError as e:
        print(f"Não foi possível ler '{caminho}': {e.strerror}")
        return 1

    try:
        # 1) Lista de tokens (opcional). Usa um léxico separado, para que o
        #    sintático comece a ler o arquivo do início.
        if "--tokens" in argumentos:
            print("TOKENS (linha:coluna  tipo  lexema)")
            for token in AnalisadorLexico(codigo).tokenizar():
                print(" ", token)
            print()

        # 2) Análise sintática. O sintático chama o léxico sob demanda, então
        #    erros léxicos também aparecem aqui, na ordem em que ocorrem.
        if "--arvore" in argumentos:
            print("ÁRVORE DE DERIVAÇÃO")
        sintatico = AnalisadorSintatico(AnalisadorLexico(codigo),
                                        rastrear="--arvore" in argumentos)
        sintatico.analisar()
    except ErroCompilacao as erro:
        print(f"{caminho}: {erro}")
        return 1

    print(f"{caminho}: programa aceito (léxica e sintaticamente correto)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
