"""Interface de linha de comando (CLI) para usar a ferramenta."""
from typing import Any
import argparse
import sys

from qual_qualis import __version__
from qual_qualis.cli.file_handler import FileHandler
from qual_qualis.data.service import DataService
from qual_qualis.index.index import Index
from qual_qualis.index.model import VenueType
from qual_qualis.index.search import SearchStrategy


class DefaultCLI:

    """Interface de linha de comando (CLI) padrão para usar a ferramenta."""

    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="qual-qualis", description="Busca de classificação Qualis."
        )
        parser.add_argument(
            "-i",
            "--input",
            help=(
                "Arquivo de entrada contendo informações para busca. "
                "São aceitos arquivos .csv e .bib."
            ),
        )
        parser.add_argument(
            "-o",
            "--output",
            help=(
                "Arquivo de saída para resultado das buscas. "
                "Se omitido, o arquivo de entrada é sobrescrito."
            ),
        )
        parser.add_argument("-q", "--query", help="String de busca individual.")
        parser.add_argument(
            "--venue-type",
            help="Especifica o tipo da via de publicação. Válido apenas para busca individual.",
            choices=["conferences", "journals"],
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Detalha a execução da ferramenta."
        )
        parser.add_argument(
            "--version", action="store_true", help="Mostra a versão da ferramenta."
        )
        self.parser = parser

    def parse_args(self, args: list[str] | None = None) -> dict[str, Any]:
        """Atalho para self.parser.parse_args()."""
        return vars(self.parser.parse_args(args))

    def run(
        self,
        input: str | None = None,  # pylint: disable=redefined-builtin
        output: str | None = None,
        query: str | None = None,
        venue_type: str | None = None,
        verbose: bool = False,
        version: bool = False,
    ):
        """Executa a CLI.

        Parâmetros
        ----------
        input : str, opcional
            Arquivo de entrada contendo informações para busca.
            São aceitos arquivos .csv e .bib.
        output : str, opcional
            Arquivo de saída para resultado das buscas.
            Se omitido, o arquivo de entrada é sobrescrito.
        query : str, opcional
            String de busca individual.
        venue_type : str, opcional
            Especifica o tipo da via de publicação.
            Válido apenas para busca individual.
        verbose : bool
            Detalha a execução da ferramenta.
        version : bool
            Mostra a versão da ferramenta.
        """
        if version:
            print(__version__)
        elif query is not None:
            self.__process_query_string(query, venue_type, verbose, input)
        elif input is not None:
            self.__process_file(input, output, verbose)
        else:
            sys.stderr.write(
                "Por favor especifique uma entrada de arquivo ou de busca.\n"
            )

    @staticmethod
    def __prepare_strategies() -> list[SearchStrategy]:
        data_service = DataService()
        index = Index(data_service)
        return [
            SearchStrategy.create("issn", index),
            SearchStrategy.create("exact", index),
            SearchStrategy.create("fuzzy", index),
        ]

    # pylint: disable=redefined-builtin
    @classmethod
    def __process_query_string(
        cls, query: str, venue_type: str | None, verbose: bool, input: str | None = None
    ):
        strategies = cls.__prepare_strategies()
        if input:
            file_handler = FileHandler.create(input)
            venues = file_handler.search_one(strategies, query)
        else:
            venue_type_e = VenueType[venue_type.upper()] if venue_type is not None else None
            venues = SearchStrategy.apply_many(strategies, issn=query, name=query,
                                               venue_type=venue_type_e)
        if not venues:
            if verbose:
                sys.stderr.write("não encontrado.\n")
            sys.exit(1)
        for venue in venues:
            print(f"{venue.qualis.name:2s} | {venue.name} | {venue.extra}")

    # pylint: disable=redefined-builtin
    @classmethod
    def __process_file(cls, input: str, output: str | None, verbose: bool):
        strategies = cls.__prepare_strategies()
        output = output or input
        file_handler = FileHandler.create(input)
        file_handler.search(strategies, verbose)
        file_handler.write(output)


def main():
    """Função a ser executada quando o módulo for chamado diretamente."""
    cli = DefaultCLI()
    cli.run(**cli.parse_args())


if __name__ == "__main__":
    main()
