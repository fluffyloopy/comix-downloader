import json
import threading
from pathlib import Path

from ..core.models import MangaInfo
from ..utils.logger import get_logger
from ..utils.session import get_session

logger = get_logger(__name__)


class KomgaMetadataWriter:
    STATUSES = ("completed", "finished", "cancel")

    _write_lock = threading.Lock()
    _written_series = set()

    def __init__(self, manga: MangaInfo, series_path):
        self.manga = manga
        self.series_path = Path(series_path)

    def write(self):
        key = str(self.series_path.resolve())
        with self._write_lock:
            if key in self._written_series:
                return
            self._written_series.add(key)

        try:
            self.series_path.mkdir(parents=True, exist_ok=True)
            series_json = self.series_path / "series.json"
            series_json.write_text(self.build_series_json(), encoding="utf-8")
            logger.info(f"Wrote series.json for '{self.manga.title}'")
            self.download_cover()
        except Exception as e:
            logger.warning(f"Failed to write Komga metadata: {e}")

    def build_series_json(self):
        metadata = {
            "type": "comicSeries",
            "publisher": "",
            "imprint": None,
            "name": self.manga.title,
            "comicid": self.manga.manga_id,
            "year": self.manga.year,
            "description_text": self.manga.description or "",
            "description_formatted": None,
            "volume": None,
            "booktype": "Print",
            "age_rating": "Adults Only 18+" if self.manga.is_nsfw else None,
            "comic_image": self.manga.poster_url or "",
            "total_issues": self.total_issues(),
            "publication_run": "",
            "status": self.map_status(),
        }
        return json.dumps({"metadata": metadata}, indent=2, ensure_ascii=False)

    def map_status(self):
        status = (self.manga.status or "").lower()
        if any(s in status for s in self.STATUSES):
            return "Ended"
        return "Continuing"

    def total_issues(self):
        try:
            if self.manga.final_chapter and float(self.manga.final_chapter) > 0:
                return int(float(self.manga.final_chapter))
        except (ValueError, TypeError):
            pass
        return None

    def download_cover(self):
        cover_path = self.series_path / "cover.jpg"
        if not self.manga.poster_url or cover_path.exists():
            return
        try:
            response = get_session().get(self.manga.poster_url, timeout=30)
            response.raise_for_status()
            tmp_path = cover_path.with_suffix(".jpg.part")
            tmp_path.write_bytes(response.content)
            tmp_path.replace(cover_path)
            logger.info(f"Saved series cover: {cover_path}")
        except Exception as e:
            logger.warning(f"Failed to download cover: {e}")