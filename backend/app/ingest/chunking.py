import hashlib
from dataclasses import dataclass


@dataclass
class Chunk:
    section: str
    text: str  # "Title > Section: body", the text that is stored and embedded


def content_hash(text: str) -> str:
    """Short fingerprint of a file's text. Same text -> same hash."""
    normalized = text.replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def build_chunks(markdown: str, max_chars: int) -> tuple[str, list[Chunk]]:
    """Split a policy file into one chunk per "##" section.

    The "# " line is the title. Text before the first "##" (for example the
    "made-up example" note) is not stored. A section longer than max_chars is
    split by paragraph, and each piece keeps the same title and heading.
    """
    title = None
    sections: list[tuple[str, list[str]]] = []

    for line in markdown.replace("\r\n", "\n").split("\n"):
        if line.startswith("# ") and title is None:
            title = line[2:].strip()
        elif line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)

    if not title:
        raise ValueError("Policy file has no '# ' title line")

    chunks: list[Chunk] = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        prefix = f"{title} > {heading}: "
        for piece in _split_by_paragraph(body, max_chars - len(prefix)):
            chunks.append(Chunk(section=heading, text=prefix + piece))
    return title, chunks


def _split_by_paragraph(body: str, max_chars: int) -> list[str]:
    if len(body) <= max_chars:
        return [body]

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if current and len(candidate) > max_chars:
            pieces.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces
