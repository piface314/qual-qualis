"""Gerencia acesso e atualização aos dados brutos do Qualis."""

from datetime import datetime, timedelta
import os
import sys

from typer import Exit
import pandas as pd

from qual_qualis.data.model import DataSource


class DataService:
    """Gerencia acesso e atualização aos dados brutos do Qualis."""

    @staticmethod
    def _cache_path(source: DataSource) -> str:
        """Retorna o caminho de arquivo de cache de acordo com a fonte de dados.

        Parâmetros
        ----------
        source : DataSource
            Fonte de dados da qual o caminho é obtido.
        """
        return os.path.join(os.path.dirname(__file__), f"{source.value}.csv")

    @staticmethod
    def _file_mod_timedelta(fp: str) -> timedelta:
        """Retorna o timedelta desde a última modificação de um arquivo.

        Parâmetros
        ----------
        fp : str
            Caminho do arquivo.
        """
        return datetime.now() - datetime.fromtimestamp(os.path.getmtime(fp))

    def last_update(self) -> datetime | None:
        """Retorna a última data de atualização dos dados."""
        fps = (self._cache_path(src) for src in DataSource)
        dts = (
            datetime.fromtimestamp(os.path.getmtime(fp))
            for fp in fps
            if os.path.exists(fp)
        )
        return max(dts, default=None)

    def get(self, source: DataSource) -> pd.DataFrame:
        """Obtém os dados brutos da classificação Qualis referentes
        a uma fonte de dados específica.

        Parâmetros
        ----------
        source : DataSource
            Fonte de dados da qual o caminho é obtido.
        """
        fp = self._cache_path(source)
        try:
            df = pd.read_csv(fp, header=0).drop_duplicates()
            return df
        except FileNotFoundError:
            sys.stderr.write(f"Fonte de dados não encontrada: {fp}\n")
            raise Exit(code=1)
