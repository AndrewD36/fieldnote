import argparse
from dataclasses import dataclass
from pathlib import Path
from research_rag.pipeline.database.db import SessionLocal
from research_rag.pipeline.database.repository import (
    PaperRepository,
)
from research_rag.pipeline.database.models import (
    PaperRecord,
)
from research_rag.pipeline.preprocessing.pdf_processor import (
    PDFProcessor,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

PROCESSED_PAPER_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "papers"
)


@dataclass
class PreprocessingStats:
    found: int = 0
    processed: int = 0
    failed: int = 0


def preprocess_paper(
    record: PaperRecord,
    repository: PaperRepository,
    processor: PDFProcessor,
    stats: PreprocessingStats,
) -> None:
    if record.pdf_path is None:
        raise ValueError(
            f"{record.arxiv_id} has "
            "no pdf_path."
        )

    pdf_path = Path(
        record.pdf_path
    )

    print(
        f"  PDF: {pdf_path}"
    )

    try:
        repository.mark_preprocessing(
            record
        )

        result = processor.process(
            arxiv_id=record.arxiv_id,
            pdf_path=pdf_path,
        )

        repository.mark_processed(
            record
        )

        stats.processed += 1

        print(
            f"  Pages: {result.page_count}"
        )

        print(
            "  Status: processed"
        )

    except Exception as exc:
        repository.mark_preprocessing_failed(
            record=record,
            error_message=str(exc),
        )

        stats.failed += 1

        print(
            f"  ERROR: "
            f"{type(exc).__name__}: {exc}"
        )


def preprocess(
    limit: int | None,
    dpi: int,
) -> PreprocessingStats:
    stats = PreprocessingStats()

    processor = PDFProcessor(
        output_root=PROCESSED_PAPER_DIR,
        dpi=dpi,
    )

    with SessionLocal() as session:
        repository = PaperRepository(
            session
        )

        papers = (
            repository
            .get_pending_preprocessing(
                limit=limit
            )
        )

        stats.found = len(papers)

        if not papers:
            return stats

        for index, record in enumerate(
            papers,
            start=1,
        ):
            print()
            print(
                f"[{index}/{len(papers)}] "
                f"{record.arxiv_id}"
            )

            print(
                f"  {record.title}"
            )

            preprocess_paper(
                record=record,
                repository=repository,
                processor=processor,
                stats=stats,
            )

    return stats


def print_summary(
    stats: PreprocessingStats,
) -> None:
    print()
    print("=" * 40)
    print("Preprocessing complete")
    print("=" * 40)

    print(
        f"Found:     {stats.found}"
    )

    print(
        f"Processed: {stats.processed}"
    )

    print(
        f"Failed:    {stats.failed}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preprocess downloaded "
            "arXiv papers."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of papers "
            "to preprocess."
        ),
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help=(
            "Page rendering DPI. "
            "Default: 150."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if (
        args.limit is not None
        and args.limit <= 0
    ):
        raise ValueError(
            "--limit must be "
            "greater than 0."
        )

    if args.dpi <= 0:
        raise ValueError(
            "--dpi must be "
            "greater than 0."
        )

    stats = preprocess(
        limit=args.limit,
        dpi=args.dpi,
    )

    print_summary(stats)


if __name__ == "__main__":
    main()