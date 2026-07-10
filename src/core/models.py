"""
Data models for manga, chapters, and configuration.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import platform


class OutputFormat(str, Enum):
    """Supported output formats."""
    IMAGES = "images"
    PDF = "pdf"
    CBZ = "cbz"

_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL",
                     *(f"COM{i}" for i in range(1, 10)),
                     *(f"LPT{i}" for i in range(1, 10))}


_MAX_NAME_BYTES = 250 if platform.system() == "Linux" else 100


def sanitize_for_path(name: str, max_bytes: int | None = None) -> str:
    limit = _MAX_NAME_BYTES if max_bytes is None else min(max_bytes, _MAX_NAME_BYTES)
    replacements = {
        ":": " -",
        "/": "-",
        "\\": "-",
        "|": "-",
        '"': "'",
        "*": "", "?": "", "<": "", ">": "",
    }
    cleaned = "".join(replacements.get(c, c) for c in name if c.isprintable())
    cleaned = " ".join(cleaned.split())

    if len(cleaned.encode("utf-8")) > limit:
        cleaned = cleaned.encode("utf-8")[:limit].decode("utf-8", errors="ignore")
        if " " in cleaned[len(cleaned) // 2:]:
            cleaned = cleaned.rsplit(" ", 1)[0]

    cleaned = cleaned.rstrip(" .")

    if cleaned.upper().split(".")[0] in _WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned or "Untitled"

@dataclass
class MangaInfo:
    """Manga information from API."""
    manga_id: Optional[int] = None
    hash_id: Optional[str] = None
    title: str = "Unknown"
    alt_titles: list[str] = field(default_factory=list)
    slug: Optional[str] = None
    rank: Optional[int] = None
    manga_type: Optional[str] = None
    poster_url: Optional[str] = None
    original_language: Optional[str] = None
    status: Optional[str] = None
    final_chapter: Optional[str] = None
    latest_chapter: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rated_avg: Optional[float] = None
    rated_count: Optional[int] = None
    follows_total: Optional[int] = None
    is_nsfw: bool = False
    year: Optional[int] = None
    genres: list = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    description: str = ""
    
    def get_safe_title(self) -> str:
        """Get filesystem-safe title."""
        return sanitize_for_path(self.title)


@dataclass
class Chapter:
    """Chapter information."""
    chapter_id: int
    number: str
    title: Optional[str] = None
    volume: Optional[str] = None
    votes: Optional[int] = None
    group_name: Optional[str] = None
    pages_count: int = 0
    
    def get_display_name(self) -> str:
        """Get chapter display name."""
        name = f"Chapter {self.number}"
        if self.title:
            name += f": {self.title}"
        return name
    
    def get_safe_folder_name(self) -> str:
        """Get filesystem-safe folder name."""
        name = f"Chapter_{self.number}"
        if self.title and self.title.strip().lower() != f"chapter {self.number}".lower():
            name += f" - {sanitize_for_path(self.title)}"
        return sanitize_for_path(name)

@dataclass
class DownloadConfig:
    """Download configuration."""
    output_format: OutputFormat = OutputFormat.IMAGES
    keep_images: bool = False
    enable_logs: bool = False
    max_chapter_workers: int = 3
    max_image_workers: int = 5
    download_path: str = "downloads"
    retry_count: int = 3
    retry_delay: float = 2.0
    headless: bool = True
    headless: bool = True
    write_metadata: bool = False
    manga_rtl: bool = True