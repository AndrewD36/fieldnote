from dataclasses import dataclass


@dataclass(frozen=True)
class TextBlock:
    block_number: int
    block_type: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


@dataclass(frozen=True)
class ProcessedPage:
    page_number: int
    width: float
    height: float
    text: str
    blocks: tuple[TextBlock, ...]
    image_path: str


@dataclass(frozen=True)
class ProcessedDocument:
    arxiv_id: str
    source_pdf_path: str
    page_count: int
    pages: tuple[ProcessedPage, ...]