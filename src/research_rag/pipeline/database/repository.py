from sqlalchemy import select
from sqlalchemy.orm import Session
from research_rag.pipeline.database.models import PaperRecord
from research_rag.pipeline.ingestion.models import Paper


class PaperRepository:
    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def get_by_arxiv_id(
        self,
        arxiv_id: str,
    ) -> PaperRecord | None:
        statement = select(PaperRecord).where(
            PaperRecord.arxiv_id == arxiv_id
        )

        return self.session.scalar(statement)

    def create(
        self,
        paper: Paper,
    ) -> PaperRecord:
        record = PaperRecord(
            arxiv_id=paper.arxiv_id,
            version=paper.version,
            title=paper.title,
            authors=list(paper.authors),
            abstract=paper.abstract,
            categories=list(paper.categories),
            primary_category=paper.primary_category,
            published_at=paper.published_at,
            updated_at=paper.updated_at,
            pdf_url=paper.pdf_url,
            download_status="pending",
            preprocessing_status="pending",
        )

        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)

        return record

    def update_metadata(
        self,
        record: PaperRecord,
        paper: Paper,
    ) -> PaperRecord:
        record.version = paper.version
        record.title = paper.title
        record.authors = list(paper.authors)
        record.abstract = paper.abstract
        record.categories = list(paper.categories)
        record.primary_category = paper.primary_category
        record.published_at = paper.published_at
        record.updated_at = paper.updated_at
        record.pdf_url = paper.pdf_url

        self.session.commit()
        self.session.refresh(record)

        return record

    def mark_pending(
        self,
        record: PaperRecord,
    ) -> None:
        record.download_status = "pending"
        record.preprocessing_status = "pending"

        record.pdf_path = None
        record.checksum = None
        record.size_bytes = None
        record.error_message = None

        self.session.commit()

    def mark_downloading(
        self,
        record: PaperRecord,
    ) -> None:
        record.download_status = "downloading"
        record.error_message = None

        self.session.commit()

    def mark_downloaded(
        self,
        record: PaperRecord,
        pdf_path: str,
        checksum: str,
        size_bytes: int,
    ) -> None:
        record.download_status = "downloaded"
        record.pdf_path = pdf_path
        record.checksum = checksum
        record.size_bytes = size_bytes
        record.error_message = None

        self.session.commit()

    def mark_failed(
        self,
        record: PaperRecord,
        error_message: str,
    ) -> None:
        record.download_status = "failed"
        record.error_message = error_message

        self.session.commit()