"""Responsável por ler dados em CSV."""
import pandas as pd

from qual_qualis.cli.file_handler.file_handler import FileHandler
from qual_qualis.index.search import SearchStrategy


class CsvHandler(FileHandler):
    """Responsável por ler dados em CSV."""

    def __init__(self) -> None:
        self.df: pd.DataFrame = None

    @classmethod
    def extension(cls) -> set[str]:
        return {"csv"}

    def read(self, fp: str):
        self.df = pd.read_csv(fp, header=0)

    def search(self, strategies: list[SearchStrategy], verbose: bool = False):
        cols = set(self.df.columns)
        keys = cols.intersection({"name", "issn"})
        assert keys
        def search(s: pd.Series):
            venue = SearchStrategy.apply_many(strategies, **{k: s[k] for k in keys})
            if venue is not None:
                print(f"{s['name']} -> {venue.qualis:2s} | {venue.name} | {venue.extra}")
                return venue.qualis
            if verbose:
                print(f"{s['name']} -> não encontrado")
            return None
        self.df = self.df.assign(qualis=lambda df: df.apply(search, axis=1))

    def write(self, fp: str):
        assert self.df
        self.df.to_csv(fp)

FileHandler.add_handler(CsvHandler)
