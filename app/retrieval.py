"""Document retrieval: split markdown files into heading-level chunks, rank with TF-IDF cosine."""
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
MIN_SCORE = 0.08


@dataclass
class Chunk:
    source: str   # file name
    title: str    # heading
    text: str


def load_chunks(kb_dir: Path = KB_DIR) -> list[Chunk]:
    chunks = []
    for path in sorted(Path(kb_dir).glob("*.md")):
        title, buf = path.stem, []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                if buf:
                    chunks.append(Chunk(path.name, title, "\n".join(buf).strip()))
                title, buf = line.lstrip("# ").strip(), []
            elif line.strip():
                buf.append(line.strip())
        if buf:
            chunks.append(Chunk(path.name, title, "\n".join(buf).strip()))
    return chunks


class Retriever:
    def __init__(self, kb_dir: Path = KB_DIR):
        self.chunks = load_chunks(kb_dir)
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vec.fit_transform([f"{c.title} {c.text}" for c in self.chunks]) if self.chunks else None

    def search(self, query: str, k: int = 3, min_score: float = MIN_SCORE) -> list[tuple[Chunk, float]]:
        if not self.chunks or not re.search(r"\w", query):
            return []
        scores = (self.matrix @ self.vec.transform([query]).T).toarray().ravel()
        order = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in order if scores[i] >= min_score]
