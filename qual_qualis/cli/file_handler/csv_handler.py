"""Responsável por ler dados em CSV."""
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

    def read(self, fp: str):
        self.df = pd.read_csv(fp, header=0)

    def search(self, strategies: list[SearchStrategy], verbose: bool = False):
        cols = set(self.df.columns)
        keys = cols.intersection({"name", "issn"})
        assert keys
        def search(s: pd.Series):
            venues = SearchStrategy.apply_many(strategies, **{k: s[k] for k in keys})
            if venues:
                venue = venues[0]
                if verbose:
                    print(f"{s['name']} -> {venue.qualis:2s} | {venue.name} | {venue.extra}")
                return venue.qualis
            if verbose:
                print(f"{s['name']} -> não encontrado")
            return None
        self.df = self.df.assign(qualis=lambda df: df.apply(search, axis=1))

    def write(self, fp: str):
        self.df.to_csv(fp)

    def search_one(self, strategies: list[SearchStrategy], key: str) -> list[Venue]:
        cols = set(self.df.columns)
        keys = cols.intersection({"name", "issn"})
        if not keys or "key" not in cols:
            return []
        entries = self.df[self.df["key"] == key]
        if len(entries) == 0:
            return []
        entry = entries.iloc[0]
        return SearchStrategy.apply_many(strategies, **{k: entry[k] for k in keys})


FileHandler.add_handler(CsvHandler)
