"""Responsável por ler dados em BibTeX."""
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

    def read(self, fp: str):
        self.library = bib.parse_file(fp)

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
        name = (journal.value if journal is not None
                else book.value if book is not None else None)
        issn = entry.fields_dict.get("issn", None)
        issn = issn.value if issn is not None else None
        return name, issn


    def search(self, strategies: list[SearchStrategy], verbose: bool = False):
        def process_block(block: bibm.Block):
            if not isinstance(block, bibm.Entry):
                return block
            name, issn = self.__read_entry(block)
            venues = SearchStrategy.apply_many(strategies, name=name, issn=issn)
            if venues:
                venue = venues[0]
                block.set_field(bibm.Field(key="qualis", value=venue.qualis))
                if verbose:
                    print(f"{name} ->\n {venue.qualis:2s} | {venue.name} | {venue.extra}\n")
            elif verbose:
                print(f"{name} ->\n não encontrado\n")
            return block

        self.library = bib.Library(map(process_block, self.library.blocks))

    def write(self, fp: str):
        bib.write_file(fp, self.library)

    def search_one(self, strategies: list[SearchStrategy], key: str) -> list[Venue]:
        entry = self.library.entries_dict.get(key)
        if not entry:
            return []
        name, issn = self.__read_entry(entry)
        return SearchStrategy.apply_many(strategies, name=name, issn=issn)


FileHandler.add_handler(BibHandler)
