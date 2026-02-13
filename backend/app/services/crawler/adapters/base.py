from abc import ABC, abstractmethod

from app.models.entities import Site
from app.services.crawler.types import NoticeSeed, ParsedNotice


class SiteAdapter(ABC):
    @abstractmethod
    def list_notices(self, site: Site, tender_types: list[str] | None = None) -> list[NoticeSeed]:
        raise NotImplementedError

    @abstractmethod
    def parse_notice(self, site: Site, seed: NoticeSeed, tender_types: list[str] | None = None) -> ParsedNotice | None:
        raise NotImplementedError

    @abstractmethod
    def download_attachment(self, site: Site, source_url: str) -> tuple[bytes, str]:
        """Returns raw bytes and mime type."""
        raise NotImplementedError

    def normalize(self, parsed: ParsedNotice) -> ParsedNotice:
        return parsed
