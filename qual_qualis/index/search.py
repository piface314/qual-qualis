"""Estratégias de busca no índice."""
from __future__ import annotations
from abc import ABC, abstractmethod
from functools import reduce

from Levenshtein import distance
from pybktree import BKTree

from qual_qualis.index.index import Index
from qual_qualis.index.model import Venue, VenueType


class SearchStrategy(ABC):
    """Estratégia de busca no índice."""

    def __init__(self, index: Index):
        self.index = index

    @abstractmethod
    def search(self, **kwargs) -> Venue | None:
        """Busca por uma via de publicação que melhor corresponde
        aos critérios de busca."""

    @classmethod
    def apply_many(cls, strategies: list[SearchStrategy], **kwargs) -> Venue | None:
        """Aplica cada uma das estratégias de busca, parando na
        primeira que encontrar uma correspondência."""
        for st in strategies:
            if result := st.search(**kwargs):
                return result
        return None

    @classmethod
    def create(cls, key: str, index: Index) -> SearchStrategy:
        """Cria uma instância de estratégia com base em seu nome.
        
        Parâmetros
        ----------
        key : str
            Nome da estratégia: "exact", "fuzzy" ou "issn".
        index : Index
            Uma instância do índice de busca.
        """
        match key:
            case "exact": return ExactSearch(index)
            case "fuzzy": return FuzzySearch(index)
            case "issn": return ISSNSearch(index)
            case _: raise KeyError(key)


class ExactSearch(SearchStrategy):
    """Busca exata pelo nome da via de publicação, usando
    normalização dos termos."""

    # pylint: disable=arguments-differ
    def search(self, name: str, venue_type: VenueType | None = None, **_) -> Venue | None:
        if not name:
            return None
        tokens = self.index.tokenize(name)
        name_hash = hash("-".join(tokens))
        fields = ["type", "hash", "name", "qualis", "extra"]
        query = (f"SELECT {', '.join(fields)}\n"
                  "  FROM venue\n"
                  "  WHERE hash = ?")
        if venue_type:
            query += f" AND type = {venue_type.value}"
        with self.index.db:
            cursor = self.index.db.execute(query, (name_hash,))
            return next((Venue(**dict(zip(fields, res))) for res in cursor), None)


class FuzzySearch(SearchStrategy):
    """Busca aproximada pelo nome da via de publicação."""

    def __init__(self, index: Index):
        super().__init__(index)
        with index.db:
            tokens = [token for token, in index.db.execute("SELECT token FROM inv_doc_frequency")]
        self.token_index = BKTree(distance, tokens)

    # pylint: disable=arguments-differ
    def search(self, name: str, venue_type: VenueType | None = None, **_) -> Venue | None:
        if not name:
            return None
        tokens = self.index.tokenize(name)
        matches = ({m for _, m in self.token_index.find(t, 1)} for t in tokens)
        matches = reduce(lambda a, b: a | b, matches, set())
        fields = ["type", "hash", "name", "qualis", "extra"]
        fields_str = ", ".join(("v." + f for f in fields))
        conditions = [f"tf.token IN ({', '.join('?' * len(matches))})"]
        if venue_type:
            conditions.append(f"v.type = {venue_type.value}")
        query = (f"SELECT {fields_str}, SUM(tf.tf * idf.idf) AS score\n"
                  "  FROM venue AS v JOIN term_frequency AS tf\n"
                  "       ON v.type = tf.venue_type AND v.hash = tf.venue_hash\n"
                  "    JOIN inv_doc_frequency AS idf ON tf.token = idf.token\n"
                 f"  WHERE {' AND '.join(conditions)}\n"
                 f"  GROUP BY {fields_str}\n"
                  "  ORDER BY score DESC\n"
                  "  LIMIT 1")
        with self.index.db:
            cursor = self.index.db.execute(query, list(matches))
            return next((Venue(**dict(zip(fields, res[:-1]))) for res in cursor), None)


class ISSNSearch(SearchStrategy):
    """Busca periódicos pelo ISSN."""

    # pylint: disable=arguments-differ
    def search(self, issn: str, **_) -> Venue | None:
        if not issn:
            return None
        fields = ["type", "hash", "name", "qualis", "extra"]
        query = (f"SELECT {', '.join(fields)}\n"
                  "  FROM venue\n"
                  "  WHERE extra = ? AND type = ?")
        with self.index.db:
            cursor = self.index.db.execute(query, (issn, VenueType.JOURNALS.value))
            return next((Venue(**dict(zip(fields, res))) for res in cursor), None)
