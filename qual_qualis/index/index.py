"""Índice que provê buscas por periódicos e conferências."""
from datetime import datetime
from functools import reduce
import hashlib
import os
import re
import sqlite3
import unicodedata

from numpy import log2
import pandas as pd

from qual_qualis.data.service import DataService, DataSource
from qual_qualis.index.model import VenueType


class Index:
    """Índice que provê buscas por periódicos e conferências."""

    @staticmethod
    def _db_path() -> str:
        """Retorna o caminho de arquivo do banco de dados."""
        return os.path.join(os.path.dirname(__file__), "index.db")

    @staticmethod
    def last_update() -> datetime | None:
        """Retorna a última data de atualização dos dados."""
        fp = Index._db_path()
        return datetime.fromtimestamp(os.path.getmtime(fp)) if os.path.exists(fp) else None

    def __init__(self, service: DataService):
        self.service = service
        should_update = self._should_update()
        self.db = sqlite3.connect(self._db_path())
        if should_update:
            self._store_index()

    def _should_update(self) -> bool:
        """Retorna se deve atualizar o banco de dados."""
        db_last_update = self.last_update()
        raw_last_update = self.service.last_update()
        return raw_last_update and (
            not db_last_update or db_last_update < raw_last_update
        )

    def _store_index(self):
        """Constroi o banco de dados do índice."""
        sql_fp = os.path.join(os.path.dirname(__file__), "create.sql")
        with open(sql_fp, encoding="utf8") as f:
            sql = f.read()
        with self.db:
            self.db.executescript(sql)
            venues_dfs, tf_dfs = zip(*(self._read_data_source(src) for src in DataSource))
            venues_df: pd.DataFrame = pd.concat(venues_dfs, axis=0)
            tf_df: pd.DataFrame = pd.concat(tf_dfs, axis=0)
            idf_df = self._calculate_idf(len(venues_df), tf_df)
            self.db.executemany("INSERT INTO venue (type, hash, name, qualis, extra) "
                                "VALUES (?, ?, ?, ?, ?)", venues_df.itertuples(index=False))
            self.db.executemany("INSERT INTO inv_doc_frequency (token, idf) "
                                "VALUES (?, ?)", idf_df.itertuples(index=False))
            self.db.executemany("INSERT INTO term_frequency (token, venue_hash, venue_type, tf) "
                                "VALUES (?, ?, ?, ?)", tf_df.itertuples(index=False))

    def _read_data_source(self, src: DataSource) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Lê uma fonte de dados com suas vias de publicação e
        os termos de busca que compõem cada uma.
        
        Parâmetros
        ----------
        src : DataSource
            Fonte de dados.
        
        Retorna
        -------
        tuple[pandas.DataFrame,pandas.DataFrame]
            Um DataFrame contendo as vias de publicação e
            outro contendo a TF (term frequency) dos termos.
        """
        df = self.service.get(src)
        extra_cols = [c for c in df.columns if c not in {"name", "qualis"}]
        venue_type = VenueType[src.name]
        extra = reduce(lambda a, b: a + b, [df[c] for c in extra_cols])
        tokens_df = (
            df.assign(extra=extra)[["name", "qualis", "extra"]]
            .assign(tokens=lambda _df: _df["name"].apply(self.tokenize))
            .assign(hash=lambda _df: _df["tokens"].apply(lambda tk: self.hash("-".join(tk))))
            .assign(type=venue_type.value)
            .drop_duplicates(subset=["hash"])
        )
        freq_df = (
            tokens_df.explode("tokens")
            .groupby(["name", "qualis", "extra", "hash", "type"])["tokens"]
            .value_counts(normalize=True).reset_index()
            .rename({"proportion": "tf", "tokens": "token"}, axis=1)
        )
        venues_df = tokens_df[["type", "hash", "name", "qualis", "extra"]]
        termf_df = freq_df[["token", "hash", "type", "tf"]]
        return venues_df, termf_df

    __tokenizer_pattern = re.compile(r"[\w'\u2019]+", re.UNICODE | re.MULTILINE | re.DOTALL)

    def tokenize(self, text: str) -> list[str]:
        """Separa uma string em seus tokens constituintes, normalizados
        para conter apenas caracteres alfanuméricos em caixa baixa.
        
        Parâmetros
        ----------
        text : str
            Texto a ser tokenizado.
        
        Retorna
        -------
        list[str]
            Lista de tokens resultantes.
        """
        tokens = self.__tokenizer_pattern.findall(text)
        tokens = (unicodedata.normalize("NFKD", token.lower()) for token in tokens)
        tokens = (re.sub(r"[^a-z0-9]", "", token) for token in tokens)
        return list(tokens)
    
    def hash(self, text: str) -> bytes:
        """Atalho para criar o hash MD5 de uma string."""
        return hashlib.md5(text.encode()).digest()

    def _calculate_idf(self, n: int, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula a IDF (inverse document frequency) de cada termo
        presente nos nomes das vias de publicação.
        
        Parâmetros
        ----------
        n : int
            Quantidade total de vias de publicação.
        df : pandas.DataFrame
            DataFrame contendo os termos e os identificadores das vias.
        
        Retorna
        -------
        pandas.DataFrame
            DataFrame contendo a IDF.
        """
        return (
            df[["token", "hash", "type"]]
            .groupby("token")["token"]
            .count().rename("count").reset_index()
            .sort_values(by="count")
            .assign(idf=lambda _df: log2(n / _df["count"]))
            [["token", "idf"]]
        )
