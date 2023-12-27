"""Gerencia acesso e atualização aos dados brutos do Qualis."""
from datetime import datetime, timedelta
import os

from google.oauth2.service_account import Credentials
import googleapiclient.discovery
import pandas as pd

from qual_qualis.data.source import DataSource


class SpreadsheetParam:
    """Define parâmetros para ler uma planilha com dados do Qualis."""

    # pylint: disable=redefined-builtin
    def __init__(self, id: str, range: str, columns: list[str]):
        self.id: str = id
        self.range: str = range
        self.columns: list[str] = columns


class DataService:
    """Gerencia acesso e atualização aos dados brutos do Qualis."""

    __spreadsheet_params = {
        DataSource.CONFERENCES: SpreadsheetParam(
            id="1yvuCa__L7r0EJy6v6Jb17fvu-VdV80PbfAReR9Gy52I",
            range="A2:C",
            columns=["acronym", "name", "qualis"]
        ),
        DataSource.JOURNALS: SpreadsheetParam(
            id="10sObNyyL7veHGFbOyizxM8oVsppQoWV-0ALrDr8FxQ0",
            range="A2:F",
            columns=["issn", "name", "", "", "", "qualis"]
        )
    }

    @staticmethod
    def __cache_path(source: DataSource) -> str:
        """Retorna o caminho de arquivo de cache de acordo com a fonte de dados.

        Parâmetros
        ----------
        source : DataSource
            Fonte de dados da qual o caminho é obtido.
        """
        return os.path.join(os.path.dirname(__file__), f"{source.value}.csv")

    @staticmethod
    def __file_mod_timedelta(fp: str) -> timedelta:
        """Retorna o timedelta desde a última modificação de um arquivo.

        Parâmetros
        ----------
        fp : str
            Caminho do arquivo.
        """
        return datetime.now() - datetime.fromtimestamp(os.path.getmtime(fp))

    def __init__(
        self,
        google_credentials: Credentials | None = None,
        update_period: timedelta = timedelta(days=7),
    ):
        """Inicializa o `DataService`.

        Parâmetros
        ----------
        google_credentials : google.oauth2.service_account.Credentials
            Credenciais de conta de serviço do Google Cloud.
        update_period : timedelta
            Período após o qual os dados devem ser atualizados.
        """
        self.google_credentials = google_credentials
        self.update_period = update_period

    def __should_update(self, fp: str) -> bool:
        """Retorna se deve atualizar o arquivo apontado por `fp`."""
        return not os.path.exists(fp) or self.__file_mod_timedelta(fp) > self.update_period

    def update(self):
        """Atualiza os dados salvos da classificação Qualis com base em
        [planilhas públicas](https://ppgcc.github.io/discentesPPGCC/pt-BR/qualis/).
        """
        assert self.google_credentials, "Cannot update data without Google Cloud credentials."
        google_service = googleapiclient.discovery.build(
            "sheets", "v4", credentials=self.google_credentials
        )
        # pylint: disable=no-member
        spreadsheets = google_service.spreadsheets()
        for src, params in self.__spreadsheet_params.items():
            result = (
                spreadsheets.values()
                .get(spreadsheetId=params.id, range=params.range)
                .execute()
            )
            values = result.get("values", [])
            df = pd.DataFrame(values, columns=params.columns)
            df = df[[c for c in params.columns if c]]
            df.to_csv(self.__cache_path(src), header=True, index=False)

    def get(self, source: DataSource) -> pd.DataFrame:
        """Obtém os dados brutos da classificação Qualis referentes
        a uma fonte de dados específica.
        
        Parâmetros
        ----------
        source : DataSource
            Fonte de dados da qual o caminho é obtido.
        """
        fp = self.__cache_path(source)
        if self.google_credentials and self.__should_update(fp):
            self.update()
        try:
            df = pd.read_csv(fp, header=0)
            return df
        except FileNotFoundError as e:
            raise FileNotFoundError("Missing Google Cloud credentials?") from e
