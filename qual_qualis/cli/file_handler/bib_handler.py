"""Responsável por ler dados em BibTeX."""

from pathlib import Path

import bibtexparser as bib
import bibtexparser.model as bibm

from qual_qualis.cli.file_handler.file_handler import FileHandler
from qual_qualis.index.model import Venue
from qual_qualis.index.search import SearchStrategy


class BibHandler(FileHandler):
    """Responsável por ler dados em BibTeX."""

    library: bib.Library = None

    @classmethod
    def extension(cls) -> set[str]:
        return {"bib"}

    def read(self, fp: Path):
        self.library = bib.parse_file(str(fp))

    @staticmethod
    def __read_entry(entry: bibm.Entry) -> tuple[str | None, str | None]:
        """Lê uma entrada do arquivo e retorna os parâmetros relevantes.

        Parâmetros
        ----------
        entry : bibtexparser.model.Entry
            Entrada de arquivo BibTeX.

        Retorna
        -------
        tuple[str | None, str | None]
            Tupla contendo o nome e o ISSN da via de publicação
        """
        journal = entry.fields_dict.get("journal", None)
        book = entry.fields_dict.get("booktitle", None)
        name = (
            journal.value
            if journal is not None
            else book.value if book is not None else None
        )
        issn = entry.fields_dict.get("issn", None)
        issn = issn.value if issn is not None else None
        return name, issn

    def search(
        self, strategies: list[SearchStrategy], n_results: int = 5
    ) -> dict[str, list[Venue]]:
        def process_block(block: bibm.Block) -> tuple[str, list[Venue]] | None:
            if not isinstance(block, bibm.Entry):
                return None
            name, issn = self.__read_entry(block)
            venues = SearchStrategy.apply_many(
                strategies, name=name, issn=issn, n_results=n_results
            )
            return block.key, venues[:n_results]

        def process_result(block: bibm.Entry, venues: list[Venue]) -> bibm.Block:
            value = "\n".join(
                f"{v.qualis.name:2s} | {v.name} | {v.extra}" for v in venues
            )
            value = f"\n{value}\n" if len(venues) > 1 else value
            block.set_field(bibm.Field(key="qualis", value=value))
            return block

        results = {
            t[0]: t[1] for t in map(process_block, self.library.blocks) if t is not None
        }
        self.library = bib.Library(
            process_result(
                block, results[block.key] if isinstance(block, bibm.Entry) else None
            )
            for block in self.library.blocks
        )
        return results

    def write(self, fp: Path):
        bib.write_file(str(fp), self.library)

    def search_one(
        self, strategies: list[SearchStrategy], key: str, n_results: int = 5
    ) -> list[Venue]:
        entry = self.library.entries_dict.get(key)
        if not entry:
            return []
        name, issn = self.__read_entry(entry)
        return SearchStrategy.apply_many(
            strategies, name=name, issn=issn, n_results=n_results
        )[:n_results]


FileHandler.add_handler(BibHandler)
