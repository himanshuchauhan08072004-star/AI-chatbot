"""Retrieval-based chatbot engine: TF-IDF (word + char n-grams) + cosine similarity."""
import json
import random
import re
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "intents.json"
THRESHOLD = 0.30


STOPWORDS = {
    "what", "is", "the", "do", "does", "you", "your", "i", "am", "are", "a", "an", "how", "to", "of",
    "me", "my", "can", "in", "it", "please", "who", "will", "for", "on", "at", "we", "be", "have", "get", "us",
}


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, drop stopwords (keep original if nothing is left)."""
    clean = re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
    kept = [w for w in clean if w not in STOPWORDS]
    return " ".join(kept or clean)


class ChatEngine:
    def __init__(self, path: Path = DATA_PATH, threshold: float = THRESHOLD):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.intents = {i["tag"]: i for i in data["intents"]}
        self.fallback = data["fallback"]
        self.threshold = threshold
        self.tags, corpus = [], []
        for intent in data["intents"]:
            for pattern in intent["patterns"]:
                self.tags.append(intent["tag"])
                corpus.append(normalize(pattern))
        self.word_vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self.matrix = hstack([self.word_vec.fit_transform(corpus), self.char_vec.fit_transform(corpus)]).tocsr()

    def predict(self, message: str):
        """Return (tag | None, confidence)."""
        text = normalize(message)
        if not text:
            return None, 0.0
        vec = hstack([self.word_vec.transform([text]), self.char_vec.transform([text])]).tocsr()
        # each block is L2-normalised, so dot/2 keeps score in [0, 1]
        scores = (self.matrix @ vec.T).toarray().ravel() / 2.0
        best = int(np.argmax(scores))
        conf = float(scores[best])
        return (self.tags[best], conf) if conf >= self.threshold else (None, conf)

    def reply(self, message: str) -> dict:
        tag, conf = self.predict(message)
        if tag is None:
            return {"reply": random.choice(self.fallback), "intent": None, "confidence": round(conf, 3)}
        return {"reply": random.choice(self.intents[tag]["responses"]), "intent": tag, "confidence": round(conf, 3)}
