from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from utils.logger.logger import logger
from utils.logger.logger_wrapper import logger_wrapper


# ── Config per source ──────────────────────────────────────────────
@dataclass
class DownloadConfig:
    url: str = ""
    path: str = ""
    id: str = ""
    extra: dict = field(default_factory=dict)


class BaseDownloader(ABC):
    def __init__(
        self, url: str = "", id: str = "", path: str = "", *args, **kwargs
    ) -> None:
        self.url = url
        self.path = path
        self.id = id
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def _download(self) -> None:
        """Download data from url."""
        pass

    @abstractmethod
    def _validate(self) -> None:
        """Validate arguments."""
        pass

    @logger_wrapper
    def execute(self) -> None:
        """Execute dowload progress."""
        logger.info(
            f"[{self.__class__.__name__}] Downloading data:\n"
            f"- url: '{self.url}'\n"
            f"- id: '{self.id}'\n"
            f"- destination: '{self.path}'"
        )
        self._validate()
        self._download()
        logger.success(f"[{self.__class__.__name__}] Complete downloading data.")
