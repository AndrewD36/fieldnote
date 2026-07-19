from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    version: int | None
    title: str
    authors: tuple[str, ...]
    abstract: str
    categories: tuple[str, ...]
    primary_category: str
    published_at: datetime
    updated_at: datetime
    pdf_url: str

    @property
    def versioned_id(self) -> str:
        if self.version is None:
            return self.arxiv_id

        return f"{self.arxiv_id}v{self.version}"