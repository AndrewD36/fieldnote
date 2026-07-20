import json
import shutil
from dataclasses import asdict
from pathlib import Path
import pymupdf
from research_rag.pipeline.preprocessing.models import (
    ProcessedDocument,
    ProcessedPage,
    TextBlock,
)


class PDFProcessor:
    def __init__(
        self,
        output_root: Path,
        dpi: int = 150,
    ) -> None:
        self.output_root = output_root
        self.dpi = dpi

        self.output_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def process(
        self,
        arxiv_id: str,
        pdf_path: Path,
    ) -> ProcessedDocument:
        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        output_dir = self.get_output_dir(
            arxiv_id
        )

        self._prepare_output_dir(
            output_dir
        )

        pages_dir = output_dir / "pages"

        pages_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        pages: list[ProcessedPage] = []

        with pymupdf.open(pdf_path) as document:
            if document.page_count == 0:
                raise ValueError(
                    f"PDF contains no pages: {pdf_path}"
                )

            for page_index in range(
                document.page_count
            ):
                page = document.load_page(
                    page_index
                )

                processed_page = self._process_page(
                    page=page,
                    page_number=page_index + 1,
                    pages_dir=pages_dir,
                )

                pages.append(
                    processed_page
                )

        processed_document = ProcessedDocument(
            arxiv_id=arxiv_id,
            source_pdf_path=str(pdf_path),
            page_count=len(pages),
            pages=tuple(pages),
        )

        self._write_document_json(
            processed_document,
            output_dir,
        )

        return processed_document

    def get_output_dir(
        self,
        arxiv_id: str,
    ) -> Path:
        safe_id = arxiv_id.replace(
            "/",
            "_",
        )

        return (
            self.output_root
            / safe_id
        )

    def _process_page(
        self,
        page: pymupdf.Page,
        page_number: int,
        pages_dir: Path,
    ) -> ProcessedPage:
        text = page.get_text(
            "text",
            sort=True,
        )

        raw_blocks = page.get_text(
            "blocks",
            sort=True,
        )

        blocks = tuple(
            self._to_text_block(block)
            for block in raw_blocks
        )

        image_path = (
            pages_dir
            / f"page_{page_number:03}.png"
        )

        pixmap = page.get_pixmap(
            dpi=self.dpi,
            alpha=False,
        )

        pixmap.save(
            str(image_path)
        )

        return ProcessedPage(
            page_number=page_number,
            width=page.rect.width,
            height=page.rect.height,
            text=text,
            blocks=blocks,
            image_path=str(image_path),
        )

    @staticmethod
    def _to_text_block(
        block: tuple,
    ) -> TextBlock:
        return TextBlock(
            x0=float(block[0]),
            y0=float(block[1]),
            x1=float(block[2]),
            y1=float(block[3]),
            text=str(block[4]).strip(),
            block_number=int(block[5]),
            block_type=int(block[6]),
        )

    @staticmethod
    def _prepare_output_dir(
        output_dir: Path,
    ) -> None:
        if output_dir.exists():
            shutil.rmtree(
                output_dir
            )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _write_document_json(
        document: ProcessedDocument,
        output_dir: Path,
    ) -> None:
        output_path = (
            output_dir
            / "document.json"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(document),
                file,
                indent=2,
                ensure_ascii=False,
            )