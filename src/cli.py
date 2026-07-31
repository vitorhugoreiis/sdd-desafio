"""CLI: orquestra carregadores → motor → serializador (plan.md §2, DESAFIO.md).

`python -m src.cli calcular --input <arquivo> --output <arquivo>`

`--politica` e `--cambio` são opcionais (T-026, T-029): o contrato fixo do
`DESAFIO.md` não ganha flag obrigatória nova, e os casos ocultos do
instrutor continuam rodando sem elas. O default de cada uma é resolvido a
partir da raiz do pacote, não do diretório de onde o comando é chamado —
senão a CLI quebraria ao rodar de outro lugar.
"""
import argparse
import sys
from pathlib import Path

from src.io.carregador import ErroDeEntrada, carregar
from src.io.carregador_cambio import carregar as carregar_cambio
from src.io.carregador_politica import carregar as carregar_politica
from src.io.serializador import salvar
from src.motor.calculadora import calcular as calcular_reembolso

RAIZ_PACOTE = Path(__file__).resolve().parent.parent
POLITICA_PADRAO = RAIZ_PACOTE / "exemplos" / "envelope" / "politica-v4.json"
CAMBIO_PADRAO = RAIZ_PACOTE / "exemplos" / "envelope" / "cambio.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="motor-reembolso")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    parser_calcular = subparsers.add_parser("calcular")
    parser_calcular.add_argument("--input", required=True, dest="entrada")
    parser_calcular.add_argument("--output", required=True, dest="saida")
    parser_calcular.add_argument("--politica", default=str(POLITICA_PADRAO), dest="politica")
    parser_calcular.add_argument("--cambio", default=str(CAMBIO_PADRAO), dest="cambio")

    args = parser.parse_args(argv)
    return _executar_calcular(args.entrada, args.saida, args.politica, args.cambio)


def _executar_calcular(caminho_entrada: str, caminho_saida: str, caminho_politica: str, caminho_cambio: str) -> int:
    try:
        solicitacao = carregar(caminho_entrada)
        politica = carregar_politica(caminho_politica)
        tabela_cambio = carregar_cambio(caminho_cambio)
    except ErroDeEntrada as erro:
        print(f"Entrada invalida: {erro}", file=sys.stderr)
        return 1

    resultado = calcular_reembolso(solicitacao, politica, tabela_cambio)
    salvar(resultado, caminho_saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
