from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
from research_rag.pipeline.ingestion.models import Paper


_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    checksum: str
    downloaded: bool
    size_bytes: int


class PDFDownloader:
    def __init__(
        self,
        root_dir: Path,
        timeout_seconds: int = 60,
    ) -> None:
        self.root_dir = root_dir
        self.timeout_seconds = timeout_seconds

        self.root_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def download(
        self,
        paper: Paper,
        overwrite: bool = False,
    ) -> DownloadResult:
        path = self.get_path(paper)

        if path.exists() and not overwrite:
            self._validate_pdf(path)

            return self._build_result(
                path=path,
                downloaded=False,
            )

        self._download_file(
            url=paper.pdf_url,
            destination=path,
        )

        try:
            self._validate_pdf(path)

        except Exception:
            path.unlink(missing_ok=True)
            raise

        return self._build_result(
            path=path,
            downloaded=True,
        )

    def get_path(
        self,
        paper: Paper,
    ) -> Path:
        safe_id = paper.arxiv_id.replace("/", "_")

        return self.root_dir / f"{safe_id}.pdf"

    def _download_file(
        self,
        url: str,
        destination: Path,
    ) -> None:
        temporary_path = destination.with_suffix(
            ".pdf.part"
        )

        request = Request(
            url,
            headers={
                "User-Agent": (
                    "research-rag/0.1 "
                    "(multimodal research project)"
                )
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                with temporary_path.open("wb") as file:
                    while chunk := response.read(
                        _CHUNK_SIZE
                    ):
                        file.write(chunk)

            temporary_path.replace(destination)

        except Exception:
            temporary_path.unlink(
                missing_ok=True
            )
            raise

    def _build_result(
        self,
        path: Path,
        downloaded: bool,
    ) -> DownloadResult:
        return DownloadResult(
            path=path,
            checksum=self._checksum(path),
            downloaded=downloaded,
            size_bytes=path.stat().st_size,
        )

    @staticmethod
    def _validate_pdf(
        path: Path,
    ) -> None:
        if not path.exists():
            raise FileNotFoundError(
                f"PDF does not exist: {path}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"PDF is empty: {path}"
            )

        with path.open("rb") as file:
            header = file.read(5)

        if header != b"%PDF-":
            raise ValueError(
                f"File is not a valid PDF: {path}"
            )

    @staticmethod
    def _checksum(
        path: Path,
    ) -> str:
        digest = sha256()

        with path.open("rb") as file:
            while chunk := file.read(
                _CHUNK_SIZE
            ):
                digest.update(chunk)

        return digest.hexdigest()