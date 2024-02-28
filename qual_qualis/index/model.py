"""Classes de modelo para o módulo de índice."""
from enum import Enum

from pydantic import BaseModel, Field

term_token_field = Field(pattern=r"^[a-z0-9]+$")


class VenueType(int, Enum):
    """Código numérico para os tipos de via de publicação."""

    CONFERENCES = 0
    JOURNALS = 1


class Qualis(str, Enum):
    """Valores da classificação Qualis."""

    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    B4 = "B4"
    C = "C"


class Venue(BaseModel):
    """Modelo de via de publicação."""

    type: VenueType
    hash: bytes
    name: str
    qualis: Qualis
    extra: str


class InvDocFrequency(BaseModel):
    """Modelo IDF."""

    token: str = term_token_field
    idf: float = 0.0


class TermFrequency(BaseModel):
    """Modelo TF."""

    term_token: str = term_token_field
    venue_type: VenueType
    venue_hash: int
    tf: float = 0.0
