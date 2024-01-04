"""Responsável por ler dados em BibTeX."""
import bibtexparser as bib
import bibtexparser.model as bibm

from qual_qualis.cli.file_handler.file_handler import FileHandler
from qual_qualis.index.search import SearchStrategy


class BibHandler(FileHandler):

    """Responsável por ler dados em BibTeX."""

    def __init__(self) -> None:
        self.library: bib.Library = None

    @classmethod
    def extension(cls) -> set[str]:
        return {"bib"}

    def read(self, fp: str):
        self.library = bib.parse_file(fp)

    def search(self, strategies: list[SearchStrategy], verbose: bool = False):
        def process_block(block: bibm.Block):
            if not isinstance(block, bibm.Entry):
                return block
            name = block.fields_dict.get("journal", None)
            name = name.value if name is not None else None
            issn = block.fields_dict.get("issn", None)
            issn = issn.value if issn is not None else None
            venue = SearchStrategy.apply_many(strategies, name=name, issn=issn)
            if venue:
                block.set_field(bibm.Field(key="qualis", value=venue.qualis))
                print(f"{name} -> {venue.qualis:2s} | {venue.name} | {venue.extra}")
            elif verbose:
                print(f"{name} -> não encontrado")
            return block

        self.library = bib.Library(map(process_block, self.library.blocks))

    def write(self, fp: str):
        assert self.library
        bib.write_file(fp, self.library)

FileHandler.add_handler(BibHandler)
