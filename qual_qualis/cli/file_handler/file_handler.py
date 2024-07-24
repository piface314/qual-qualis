"""Classe abstrata para lidar com diferentes tipos de arquivo de entrada."""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
import re
import os

from qual_qualis.index.search import SearchStrategy
from qual_qualis.index.model import Venue


class FileHandler(ABC):

    """Classe abstrata para lidar com diferentes tipos de arquivo de entrada."""

    __supported_extensions: dict[str, type[FileHandler]] = {}

    @classmethod
    def add_handler(cls, handler: type[FileHandler]):
        """Associa uma subclasse às extensões que suporta.
        
        Parâmetros
        ----------
        handler : type[FileHandler]
            Subclasse de FileHandler.
        """
        for ext in handler.extension():
            cls.__supported_extensions[ext] = handler

    @classmethod
    def create(cls, fp: Path) -> FileHandler:
        """Cria uma instância de FileHandler de acordo com
        um caminho de arquivo que termina em alguma extensão
        compreendida.
        
        Parâmetros
        ----------
        fp : str
            Caminho de arquivo.

        Retorna
        -------
        FileHandler
            Instância de FileHandler.
        """
        name = os.path.basename(fp)
        m = re.search(r"\.(.+)$", name)
        ext = m.group(1) if m is not None else None
        return cls.__supported_extensions[ext](fp)

    def __init__(self, fp: str):
        self.read(fp)

    @classmethod
    @abstractmethod
    def extension(cls) -> set[str]:
        """Retorna as extensões de arquivo compreendidas pela classe."""

    @abstractmethod
    def read(self, fp: Path):
        """Lê um arquivo e salva suas informações para consulta posterior.
        
        Parâmetros
        ----------
        fp : Path
            Caminho de arquivo a ser lido.
        """

    @abstractmethod
    def search(self, strategies: list[SearchStrategy], n_results: int = 5) -> dict[str, list[Venue]]:
        """Realiza buscas para cada entrada contida no arquivo lido,
        atualizando os dados salvos com o resultado da busca.
        
        Parâmetros
        ----------
        strategies : list[SearchStrategy]
            Lista de estratégias de busca a ser usadas.
        n_results: int, opcional
            Quantidade de resultados.
        """

    @abstractmethod
    def write(self, fp: Path):
        """Escreve em arquivo os resultados da busca.
        
        Parâmetros
        ----------
        fp : Path
            Caminho de arquivo a ser escrito.
        """

    @abstractmethod
    def search_one(self, strategies: list[SearchStrategy], key: str, n_results: int = 5) -> list[Venue]:
        """Realiza a busca para uma entrada específica no arquivo lido.

        Parâmetros
        ----------
        strategies : list[SearchStrategy]
            Lista de estratégias de busca a ser usadas.
        key : str
            Chave identificadora da entrada a ser pesquisada.
        n_results: int, opcional
            Quantidade de resultados.

        Retorna
        -------
        list[Venue]
            Resultados da busca.
        """
