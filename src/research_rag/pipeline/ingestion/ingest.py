import argparse
from dataclasses import dataclass
from pathlib import Path
from research_rag.pipeline.database.db import SessionLocal
from research_rag.pipeline.database.models import PaperRecord
from research_rag.pipeline.database.repository import PaperRepository
from research_rag.pipeline.ingestion.arxiv_client import ArxivClient
from research_rag.pipeline.ingestion.downloader import PDFDownloader
from research_rag.pipeline.ingestion.models import Paper


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PDF_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "papers"
)


@dataclass
class IngestionStats:
    found: int = 0
    new: int = 0
    updated: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0


def is_newer_version(
    paper: Paper,
    record: PaperRecord,
) -> bool:
    if paper.version is None:
        return False

    if record.version is None:
        return True

    return paper.version > record.version


def ingest_paper(
    paper: Paper,
    repository: PaperRepository,
    downloader: PDFDownloader,
    stats: IngestionStats,
) -> None:
    record = repository.get_by_arxiv_id(
        paper.arxiv_id
    )

    #
    # NEW PAPER
    #
    if record is None:
        print("  New paper")

        record = repository.create(paper)

        stats.new += 1

        should_download = True
        overwrite = False

    #
    # EXISTING PAPER
    #
    else:
        newer_version = is_newer_version(
            paper,
            record,
        )

        if newer_version:
            print(
                f"  New version: "
                f"v{record.version} -> v{paper.version}"
            )

            repository.update_metadata(
                record,
                paper,
            )

            repository.mark_pending(record)

            stats.updated += 1

            should_download = True
            overwrite = True

        elif record.download_status != "downloaded":
            print(
                f"  Previous status: "
                f"{record.download_status}"
            )

            repository.update_metadata(
                record,
                paper,
            )

            should_download = True
            overwrite = True

        else:
            repository.update_metadata(
                record,
                paper,
            )

            if (
                record.pdf_path is None
                or not Path(record.pdf_path).exists()
            ):
                print(
                    "  Database says downloaded, "
                    "but PDF is missing."
                )

                should_download = True
                overwrite = True

            else:
                should_download = False
                overwrite = False

    #
    # SKIP
    #
    if not should_download:
        print("  Status: already downloaded")

        stats.skipped += 1
        return

    #
    # DOWNLOAD
    #
    try:
        repository.mark_downloading(record)

        result = downloader.download(
            paper,
            overwrite=overwrite,
        )

        repository.mark_downloaded(
            record=record,
            pdf_path=str(result.path),
            checksum=result.checksum,
            size_bytes=result.size_bytes,
        )

        size_mb = (
            result.size_bytes
            / (1024 * 1024)
        )

        print("  Status: downloaded")
        print(f"  File:   {result.path}")
        print(f"  Size:   {size_mb:.2f} MB")
        print(f"  SHA256: {result.checksum}")

        stats.downloaded += 1

    except Exception as exc:
        repository.mark_failed(
            record=record,
            error_message=str(exc),
        )

        stats.failed += 1

        print(
            f"  ERROR: "
            f"{type(exc).__name__}: {exc}"
        )


def ingest(
    category: str,
    max_results: int,
) -> IngestionStats:

    client = ArxivClient()

    downloader = PDFDownloader(
        root_dir=RAW_PDF_DIR
    )

    stats = IngestionStats()

    with SessionLocal() as session:
        repository = PaperRepository(session)

        papers = client.search_latest(
            category=category,
            max_results=max_results,
        )

        for paper in papers:
            stats.found += 1

            print()
            print(
                f"[{stats.found}/{max_results}] "
                f"{paper.versioned_id}"
            )

            print(f"  {paper.title}")

            ingest_paper(
                paper=paper,
                repository=repository,
                downloader=downloader,
                stats=stats,
            )

    return stats


def print_summary(
    stats: IngestionStats,
) -> None:
    print()
    print("=" * 40)
    print("Ingestion complete")
    print("=" * 40)

    print(f"Found:      {stats.found}")
    print(f"New:        {stats.new}")
    print(f"Updated:    {stats.updated}")
    print(f"Downloaded: {stats.downloaded}")
    print(f"Skipped:    {stats.skipped}")
    print(f"Failed:     {stats.failed}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest recent arXiv papers "
            "into the research corpus."
        )
    )

    parser.add_argument(
        "--category",
        default="cs.LG",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.max_results <= 0:
        raise ValueError(
            "--max-results must be greater than 0."
        )

    stats = ingest(
        category=args.category,
        max_results=args.max_results,
    )

    print_summary(stats)


if __name__ == "__main__":
    main()