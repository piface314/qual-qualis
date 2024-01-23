"""Gerencia acesso e atualização aos dados brutos do Qualis."""
from datetime import datetime, timedelta
import os

from google.oauth2.service_account import Credentials
import googleapiclient.discovery
import pandas as pd

from qual_qualis.data.model import SpreadsheetParam, DataSource


class DataService:
    """Gerencia acesso e atualização aos dados brutos do Qualis."""

    spreadsheet_params = {
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

    def __init__(
        self,
        credentials_fp: str | None = None,
        update_period: timedelta = timedelta(days=7),
    ):
        """Inicializa o `DataService`.

        Parâmetros
        ----------
        credentials_fp : str
            Credenciais de conta de serviço do Google Cloud.
        update_period : timedelta
            Período após o qual os dados devem ser atualizados.
        """
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials_fp = credentials_fp or self.default_credentials_fp()
        self.credentials = Credentials.from_service_account_file(credentials_fp, scopes=scopes)
        self.update_period = update_period

    @staticmethod
    def default_credentials_fp() -> str:
        """Retorna a localização padrão das credenciais Google.
        
        Para sistemas Linux e Mac, esse caminho é `$HOME/.config/qual-qualis/google-credentials.json`.
        Para sistemas Windows, esse caminho é `%LOCALAPPDATA%\\qual-qualis\\google-credentials.json`.
        """
        if os.name == "posix":
            prefix = os.path.join(os.environ.get("HOME"), ".config")
        else:
            prefix = os.environ.get("LOCALAPPDATA")
        return os.path.join(prefix, "qual-qualis", "google-credentials.json")

    def _should_update(self, fp: str) -> bool:
        """Retorna se deve atualizar o arquivo apontado por `fp`."""
        return False
        return not os.path.exists(fp) or self._file_mod_timedelta(fp) > self.update_period

    def last_update(self) -> datetime | None:
        """Retorna a última data de atualização dos dados."""
        fps = (self._cache_path(src) for src in self.spreadsheet_params)
        dts = (datetime.fromtimestamp(os.path.getmtime(fp)) for fp in fps if os.path.exists(fp))
        return max(dts, default=None)

    def update(self):
        """Atualiza os dados salvos da classificação Qualis com base em
        [planilhas públicas](https://ppgcc.github.io/discentesPPGCC/pt-BR/qualis/).
        """
        assert self.credentials, "Cannot update data without Google Cloud credentials."
        google_service = googleapiclient.discovery.build(
            "sheets", "v4", credentials=self.credentials
        )
        # pylint: disable=no-member
        spreadsheets = google_service.spreadsheets()
        for src, params in self.spreadsheet_params.items():
            result = (
                spreadsheets.values()
                .get(spreadsheetId=params.id, range=params.range)
                .execute()
            )
            values = result.get("values", [])
            df = pd.DataFrame(values, columns=params.columns)
            df = df[params.used_columns()]
            df.to_csv(self._cache_path(src), header=True, index=False)

    def get(self, source: DataSource) -> pd.DataFrame:
        """Obtém os dados brutos da classificação Qualis referentes
        a uma fonte de dados específica.
        
        Parâmetros
        ----------
        source : DataSource
            Fonte de dados da qual o caminho é obtido.
        """
        fp = self._cache_path(source)
        if self.credentials and self._should_update(fp):
            self.update()
        try:
            df = pd.read_csv(fp, header=0).drop_duplicates()
            return df
        except FileNotFoundError as e:
            raise FileNotFoundError("Missing Google Cloud credentials?") from e

