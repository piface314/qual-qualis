"""Classes de modelo para o módulo de dados brutos."""
from enum import Enum


class DataSource(str, Enum):
    """Define as fontes de dados disponíveis.

    A classificação Qualis define critérios para conferências/eventos
    e também para periódicos, sendo essas as duas fontes de dados.
    """

    CONFERENCES = "conferences"
    JOURNALS = "journals"
