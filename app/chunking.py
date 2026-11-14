"""
app/chunking.py — Document Chunker
-------------------------------------
Loads ArduinoMate source documents and splits them into overlapping text
chunks.  Every chunk carries structured metadata:

    source  : relative file path (e.g. "ArduinoMate/data/raw/pinMode.adoc")
    title   : function name extracted from the document (e.g. "pinMode()")
    page    : 1-based section index within the document
    category: Arduino category (e.g. "Digital I/O")

Supported sources
-----------------
1. data/raw/*.adoc  — real Arduino reference files (AsciiDoc format)
2. data/records.json — the 20-record structured knowledge base

Chunking strategy
-----------------
- Each AsciiDoc *section* (Description, Parameters, Example Code,
  Notes and Warnings) becomes its own chunk (page = section index).
- Chunks shorter than MIN_CHARS are merged with the next section.
- Chunks longer than MAX_CHARS are split on sentence boundaries.
"""

import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Tuneable constants
# ---------------------------------------------------------------------------
MIN_CHARS = 60    # merge section into next if shorter than this
MAX_CHARS = 500   # split section if longer than this

# Root of the GENAI workspace (parent of this app/ directory)
BASE_DIR    = Path(__file__).resolve().parent.parent
RAW_DIR     = BASE_DIR / "ArduinoMate" / "data" / "raw"
RECORDS_FILE = BASE_DIR / "ArduinoMate" / "data" / "records.json"


# ---------------------------------------------------------------------------
# AsciiDoc helpers
# ---------------------------------------------------------------------------
_ADOC_MARKUP = re.compile(
    r"\[source,arduino\]|-{4,}|"               # code fence markers
    r"\[%hardbreaks\]|\[float\]|\[#\w+\]|"     # adoc attributes
    r"//.*?$|"                                  # single-line comments
    r"\[options=\"header\"\]|"                  # table headers
    r"link:[^\[]+\[[^\]]*\]|"                   # link:...[...]
    r"http\S+\[[^\]]*\]|"                       # http...[...]
    r"#EXAMPLE#\s*|#LANGUAGE#\s*|"              # role tags
    r"\[role=\"[^\"]+\"\]|"                     # role attributes
    r"\*[A-Z]+\*\s*",                           # bold ALL-CAPS markers
    re.MULTILINE | re.IGNORECASE,
)
# Strip entire AsciiDoc table blocks  |===...===|
_ADOC_TABLE = re.compile(r"\|={3,}.*?\|={3,}", re.DOTALL)

_BACKTICK = re.compile(r"`([^`]+)`")
_UNDERSCORE = re.compile(r"_([^_]+)_")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_HEADER_LINE = re.compile(r"^=+\s+\w")


_FRONTMATTER = re.compile(r"^---.*?---\s*", re.DOTALL)
_SECTION_COMMENTS = re.compile(r"//\s*(OVERVIEW|HOW TO USE|SEE ALSO)\s+SECTION\s+(STARTS|ENDS)", re.IGNORECASE)


def _clean(text: str) -> str:
    """Strip AsciiDoc markup, front-matter and normalise whitespace."""
    # Remove YAML front-matter block
    text = _FRONTMATTER.sub("", text)
    # Remove full table blocks first (before line-by-line markup stripping)
    text = _ADOC_TABLE.sub("", text)
    # Remove section comment markers
    text = _SECTION_COMMENTS.sub("", text)
    text = _ADOC_MARKUP.sub(" ", text)
    text = _BACKTICK.sub(r"\1", text)
    text = _UNDERSCORE.sub(r"\1", text)
    # Remove leftover -- block markers and stray | characters
    text = re.sub(r"(?m)^\s*--\s*$", "", text)
    text = re.sub(r"\|", " ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def _extract_title(adoc_text: str) -> str:
    """Pull the function title from the front-matter or first heading."""
    m = re.search(r"^title:\s*(.+)$", adoc_text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    m = re.search(r"^=\s+(.+)$", adoc_text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "Unknown"


def _extract_category(adoc_text: str) -> str:
    """Pull the sub-category from front-matter."""
    m = re.search(r'subCategories:\s*\[\s*"([^"]+)"', adoc_text)
    if m:
        return m.group(1).strip()
    return "General"


def _split_into_sections(adoc_text: str) -> list[str]:
    """
    Split on AsciiDoc === section headers.
    Returns a list of (cleaned) section text strings.
    """
    # Split on === Section headers
    parts = re.split(r"(?m)^={3}\s+", adoc_text)
    sections: list[str] = []
    for part in parts:
        cleaned = _clean(part)
        if len(cleaned) >= MIN_CHARS:
            sections.append(cleaned)
        elif sections:
            # Merge short section into previous
            sections[-1] += " " + cleaned
    return sections


def _split_long(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Split a text that is too long on sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for s in sentences:
        if len(current) + len(s) + 1 <= max_chars:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks if chunks else [text[:max_chars]]


# ---------------------------------------------------------------------------
# Public chunk type
# ---------------------------------------------------------------------------
class Chunk:
    """A single document chunk with text and metadata."""

    __slots__ = ("text", "source", "title", "page", "category", "chunk_id")

    def __init__(
        self,
        text: str,
        source: str,
        title: str,
        page: int,
        category: str,
        chunk_id: str,
    ) -> None:
        self.text      = text
        self.source    = source
        self.title     = title
        self.page      = page
        self.category  = category
        self.chunk_id  = chunk_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text":     self.text,
            "source":   self.source,
            "title":    self.title,
            "page":     self.page,
            "category": self.category,
        }

    def __repr__(self) -> str:
        return f"Chunk(id={self.chunk_id!r}, title={self.title!r}, page={self.page})"


# ---------------------------------------------------------------------------
# Source loaders
# ---------------------------------------------------------------------------
def _chunks_from_adoc(path: Path) -> list[Chunk]:
    """Parse one .adoc file into a list of Chunk objects."""
    raw      = path.read_text(encoding="utf-8", errors="ignore")
    title    = _extract_title(raw)
    category = _extract_category(raw)
    source   = str(path.relative_to(BASE_DIR)).replace("\\", "/")
    sections = _split_into_sections(raw)

    chunks: list[Chunk] = []
    page = 1
    for section in sections:
        for sub in _split_long(section):
            if len(sub.strip()) < MIN_CHARS:
                continue
            chunks.append(
                Chunk(
                    text=sub.strip(),
                    source=source,
                    title=title,
                    page=page,
                    category=category,
                    chunk_id=f"{path.stem}_p{page}_{len(chunks)}",
                )
            )
            page += 1

    return chunks


def _chunks_from_records(path: Path) -> list[Chunk]:
    """
    Turn each field of every records.json entry into its own chunk.
    Fields: description, common_gotcha, syntax, returns.
    """
    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    source  = str(path.relative_to(BASE_DIR)).replace("\\", "/")
    chunks: list[Chunk] = []

    for rec in records:
        fn_name  = rec.get("function_name", "unknown")
        category = rec.get("category", "General")
        base_id  = f"rec_{fn_name.replace('.', '_').replace(' ', '_')}"

        field_map = {
            1: ("description",   rec.get("description") or ""),
            2: ("syntax",        f"Syntax: {rec.get('syntax', '')}. Returns: {rec.get('returns', '')}"),
            3: ("common_gotcha", rec.get("common_gotcha") or ""),
        }

        for page, (field_name, text) in field_map.items():
            text = text.strip()
            if len(text) < MIN_CHARS:
                continue
            for sub in _split_long(text):
                if len(sub.strip()) < MIN_CHARS:
                    continue
                chunks.append(
                    Chunk(
                        text=sub.strip(),
                        source=source,
                        title=fn_name,
                        page=page,
                        category=category,
                        chunk_id=f"{base_id}_f{field_name[0]}{page}_{len(chunks)}",
                    )
                )

    return chunks


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def load_all_chunks() -> list[Chunk]:
    """
    Load and chunk all ArduinoMate documents.

    Returns:
        A flat list of Chunk objects from .adoc files + records.json.
    """
    chunks: list[Chunk] = []

    # 1. .adoc files
    if RAW_DIR.exists():
        for adoc_file in sorted(RAW_DIR.glob("*.adoc")):
            try:
                chunks.extend(_chunks_from_adoc(adoc_file))
            except Exception as exc:
                print(f"[chunking] WARNING: skipped {adoc_file.name}: {exc}")

    # 2. records.json
    if RECORDS_FILE.exists():
        try:
            chunks.extend(_chunks_from_records(RECORDS_FILE))
        except Exception as exc:
            print(f"[chunking] WARNING: skipped records.json: {exc}")

    print(f"[chunking] Loaded {len(chunks)} chunks from {len(set(c.source for c in chunks))} sources.")
    return chunks


if __name__ == "__main__":
    all_chunks = load_all_chunks()
    print(f"\nTotal chunks: {len(all_chunks)}")
    for c in all_chunks[:5]:
        print(f"  {c.chunk_id:40s} | page={c.page} | {c.text[:60]}...")
