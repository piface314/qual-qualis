"""Classes de modelo para o módulo de dados brutos."""
from enum import Enum

from pydantic import BaseModel


class SpreadsheetParam(BaseModel):
    """Define parâmetros para ler uma planilha com dados do Qualis."""

    id: str
    range: str
    columns: list[str]

    def used_columns(self) -> list[str]:
        """Retorna as colunas que são de fato usadas."""
        return [c for c in self.columns if c]


class DataSource(str, Enum):
    """Define as fontes de dados disponíveis.

    A classificação Qualis define critérios para conferências/eventos
    e também para periódicos, sendo essas as duas fontes de dados.
    """

    CONFERENCES = "conferences"
    JOURNALS = "journals"
