"""Responsável por ler dados em CSV."""

from pathlib import Path
import sys

from typer import Exit
import pandas as pd

from qual_qualis.cli.file_handler.file_handler import FileHandler
from qual_qualis.index.model import Venue
from qual_qualis.index.search import SearchStrategy


class CsvHandler(FileHandler):
    """Responsável por ler dados em CSV."""

    df: pd.DataFrame = None

    @classmethod
    def extension(cls) -> set[str]:
        return {"csv"}

    def read(self, fp: Path):
        self.df = pd.read_csv(fp, header=0)
        if not "key" in self.df.columns or not self.param_columns():
            sys.stderr.write(
                f"O arquivo .csv de entrada deve conter a coluna `key` "
                "e alguma coluna de busca válida (`name`, `issn`).\n"
            )
            raise Exit(code=1)

    def param_columns(self) -> set[str]:
        return set(self.df.columns) & {"name", "issn"}

    def search(
        self, strategies: list[SearchStrategy], n_results: int = 5
    ) -> dict[str, list[Venue]]:
        keys = self.param_columns()

        def search(s: pd.Series):
            venues = SearchStrategy.apply_many(strategies, **{k: s[k] for k in keys})
            return venues[:n_results]

        def format(venues: list[Venue]) -> str:
            return " / ".join(f"{v.qualis.name} ({v.name} {v.extra})" for v in venues)

        results = [
            (key, venues)
            for key, venues in zip(self.df["key"], self.df.apply(search, axis=1))
        ]
        self.df = self.df.assign(qualis=[format(venues) for _, venues in results])
        return {key: venues for key, venues in results}

    def write(self, fp: Path):
        self.df.to_csv(fp)

    def search_one(
        self, strategies: list[SearchStrategy], key: str, n_results: int = 5
    ) -> list[Venue]:
        keys = self.param_columns()
        entries = self.df[self.df["key"] == key]
        if len(entries) == 0:
            return []
        entry = entries.iloc[0]
        return SearchStrategy.apply_many(
            strategies, **{k: entry[k] for k in keys}, n_results=n_results
        )


FileHandler.add_handler(CsvHandler)
