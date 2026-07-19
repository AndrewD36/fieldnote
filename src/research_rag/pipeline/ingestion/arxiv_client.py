import re
from collections.abc import Iterator
import arxiv
from research_rag.pipeline.ingestion.models import Paper


_VERSION_PATTERN = re.compile(r"^(?P<id>.+?)v(?P<version>\d+)$")


class ArxivClient:
    def __init__(
        self,
        page_size: int = 100,
        delay_seconds: float = 3.0,
        num_retries: int = 3,
    ) -> None:
        self._client = arxiv.Client(
            page_size=page_size,
            delay_seconds=delay_seconds,
            num_retries=num_retries,
        )

    def search_latest(
        self,
        category: str,
        max_results: int = 100,
    ) -> Iterator[Paper]:
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        for result in self._client.results(search):
            yield self._to_paper(result)

    def _to_paper(
        self,
        result: arxiv.Result,
    ) -> Paper:
        arxiv_id, version = self._parse_arxiv_id(
            result.get_short_id()
        )

        if result.pdf_url is None:
            raise ValueError(
                f"Paper {arxiv_id} does not have a PDF URL."
            )

        return Paper(
            arxiv_id=arxiv_id,
            version=version,
            title=result.title.strip(),
            authors=tuple(
                author.name
                for author in result.authors
            ),
            abstract=result.summary.strip(),
            categories=tuple(result.categories),
            primary_category=result.primary_category,
            published_at=result.published,
            updated_at=result.updated,
            pdf_url=result.pdf_url,
        )

    @staticmethod
    def _parse_arxiv_id(
        value: str,
    ) -> tuple[str, int | None]:
        match = _VERSION_PATTERN.match(value)

        if match is None:
            return value, None

        arxiv_id = match.group("id")
        version = int(match.group("version"))

        return arxiv_id, version