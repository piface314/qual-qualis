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


class ExactSearch(SearchStrategy):
    """Busca exata pelo nome da via de publicação, usando
    normalização dos termos."""

    # pylint: disable=arguments-differ
    def search(self, name: str, **_) -> Venue | None:
        tokens = self.index.tokenize(name)
        slug = "-".join(tokens)
        fields = ["type", "slug", "name", "qualis", "extra"]
        query = (f"SELECT {', '.join(fields)}\n"
                  "  FROM venue\n"
                  "  WHERE slug = ?")
        with self.index.db:
            cursor = self.index.db.execute(query, (slug,))
            return next((Venue(**dict(zip(fields, res))) for res in cursor), None)


class FuzzySearch(SearchStrategy):
    """Busca aproximada pelo nome da via de publicação."""

    def __init__(self, index: Index):
        super().__init__(index)
        with index.db:
            tokens = [token for token, in index.db.execute("SELECT token FROM inv_doc_frequency")]
        self.token_index = BKTree(distance, tokens)

    # pylint: disable=arguments-differ
    def search(self, name: str, **_) -> Venue | None:
        tokens = self.index.tokenize(name)
        matches = ({m for _, m in self.token_index.find(t, 1)} for t in tokens)
        matches = reduce(lambda a, b: a | b, matches, set())
        fields = ["type", "slug", "name", "qualis", "extra"]
        fields_str = ", ".join(("v." + f for f in fields))
        query = (f"SELECT {fields_str}, SUM(tf.tf * idf.idf) AS score\n"
                  "  FROM venue AS v JOIN term_frequency AS tf\n"
                  "       ON v.type = tf.venue_type AND v.slug = tf.venue_slug\n"
                  "    JOIN inv_doc_frequency AS idf ON tf.token = idf.token\n"
                  f"  WHERE tf.token IN ({', '.join('?' * len(matches))})\n"
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
        fields = ["type", "slug", "name", "qualis", "extra"]
        query = (f"SELECT {', '.join(fields)}\n"
                  "  FROM venue\n"
                  "  WHERE extra = ? AND type = ?")
        with self.index.db:
            cursor = self.index.db.execute(query, (issn, VenueType.JOURNALS.value))
            return next((Venue(**dict(zip(fields, res))) for res in cursor), None)
