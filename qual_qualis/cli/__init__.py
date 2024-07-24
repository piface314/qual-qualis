"""Interface de linha de comando (CLI) para usar a ferramenta."""

from pathlib import Path
from typing import Annotated, Optional
from typer import Argument, Exit, Option, Typer
import sys

from qual_qualis import __version__
from qual_qualis.cli.file_handler import FileHandler
from qual_qualis.data.service import DataService, DataSource
from qual_qualis.index.index import Index
from qual_qualis.index.model import Venue, VenueType
from qual_qualis.index.search import SearchStrategy, SearchStrategyKey


cli = Typer(name="qual-qualis")


@cli.command()
def search(
    query: Annotated[
        Optional[str], Argument(help="String de busca individual.")
    ] = None,
    input_file: Annotated[
        Optional[Path],
        Option(
            "--input",
            "-i",
            help=(
                "Arquivo de entrada contendo informações para busca. "
                "São aceitos arquivos .csv e .bib."
            ),
        ),
    ] = None,
    output_file: Annotated[
        Optional[Path],
        Option(
            "--output",
            "-o",
            help=(
                "Arquivo de saída para resultado das buscas. "
                "Se omitido, os resultados são apresentados na tela."
            ),
        ),
    ] = None,
    venue: Annotated[
        Optional[DataSource],
        Option(
            help=(
                "Especifica o tipo da via de publicação. "
                "Válido apenas para busca individual."
            ),
        ),
    ] = None,
    strategies: Annotated[
        list[SearchStrategyKey],
        Option("-s", "--strategy", help="Estratégias de busca a ser usadas."),
    ] = [],
    n_results: Annotated[
        int, Option("-n", help="Quantidade de resultados a ser exibidos.")
    ] = 5,
    version: Annotated[
        bool, Option("-v", "--version", help="Mostra a versão da ferramenta.")
    ] = False,
):
    """Busca de classificação Qualis."""
    if version:
        return print(__version__)

    venue_type = VenueType[venue.name] if venue is not None else None
    strategies = strategies if strategies else list(SearchStrategyKey)

    match (query, input_file):
        case (None, None):
            sys.stderr.write(
                "Por favor especifique uma string de busca ou arquivo de entrada.\n"
            )
            raise Exit(code=1)
        case (query, None):
            simple_search(strategies, query, venue_type, n_results)
        case (None, input_file):
            file_search(strategies, input_file, output_file, n_results)
        case (query, input_file):
            file_single_search(strategies, input_file, query, n_results)


def prepare_strategies(keys: list[SearchStrategyKey]) -> list[SearchStrategy]:
    """Inicializa e retorna as estratégias de busca."""
    data_service = DataService()
    index = Index(data_service)
    return [SearchStrategy.create(key, index) for key in keys]


def show_results(venues: list[Venue], indent_level: int = 0):
    """Exibe resultados de busca."""
    indent = " " * indent_level
    for venue in venues:
        print(f"{indent}- {venue.qualis.name:2s} | {venue.name} | {venue.extra}")


def simple_search(
    strategies: list[SearchStrategyKey],
    query: str,
    venue_type: VenueType | None,
    n_results: int,
):
    """Realiza busca individual."""
    strategies = prepare_strategies(strategies)
    venues = SearchStrategy.apply_many(
        strategies, issn=query, name=query, venue_type=venue_type, n_results=n_results
    )
    if not venues:
        Exit(code=1)
    show_results(venues)


def file_search(
    strategies: list[SearchStrategyKey],
    input_file: Path,
    output_file: Path | None,
    n_results: int,
):
    strategies = prepare_strategies(strategies)
    file_handler = FileHandler.create(input_file)
    results = file_handler.search(strategies, n_results=n_results)
    if output_file:
        file_handler.write(output_file)
    else:
        for key, venues in results.items():
            print(f"{key}:")
            show_results(venues, indent_level=2)


def file_single_search(
    strategies: list[SearchStrategyKey], input_file: Path, key: str, n_results: int
):
    strategies = prepare_strategies(strategies)
    file_handler = FileHandler.create(input_file)
    venues = file_handler.search_one(strategies, key, n_results=n_results)
    if not venues:
        Exit(code=1)
    show_results(venues)


def main():
    cli()


if __name__ == "__main__":
    main()
