import os
from typing import List, Tuple, Optional, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np

_FAQ_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge", "faq_general_fr.md")

_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

class FaqEntry:
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.vector = None

    def embed(self):
        if self.vector is None:
            self.vector = _embeddings.embed_query(self.title + "\n" + self.content)
        return self.vector


def _load_faq_entries() -> List[FaqEntry]:
    if not os.path.exists(_FAQ_PATH):
        return []
    with open(_FAQ_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    # Simple splitter: sections start with '### '
    parts = [p.strip() for p in text.split("\n### ") if p.strip()]
    entries: List[FaqEntry] = []
    for i, part in enumerate(parts):
        if i == 0 and part.lower().startswith("### "):
            # If the very first chunk still contains a heading marker
            part = part[4:]
        if "\n" in part:
            title, body = part.split("\n", 1)
        else:
            title, body = part, ""
        entries.append(FaqEntry(title.strip(), body.strip()))
    # Fallback: if the splitter failed, put the entire content as one entry
    if not entries:
        entries.append(FaqEntry("FAQ Assurance Santé Tunisie", text))
    for e in entries:
        e.embed()
    return entries

_FAQ_ENTRIES: List[FaqEntry] = _load_faq_entries()


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    a_vec = np.array(a)
    b_vec = np.array(b)
    denom = (np.linalg.norm(a_vec) * np.linalg.norm(b_vec))
    if denom == 0:
        return 0.0
    return float(np.dot(a_vec, b_vec) / denom)


def search_faq(question: str, top_k: int = 2) -> List[Tuple[FaqEntry, float]]:
    if not question or not _FAQ_ENTRIES:
        return []
    q_vec = _embeddings.embed_query(question)
    scored = [(entry, _cosine_similarity(q_vec, entry.vector)) for entry in _FAQ_ENTRIES]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def get_faq_answer_if_relevant(question: str, threshold: float = 0.48) -> Optional[Dict[str, str]]:
    """
    Returns an answer dict if the FAQ contains a relevant entry for the question.
    Dict fields: {"title", "answer", "source"}
    """
    hits = search_faq(question, top_k=2)
    if not hits:
        return None
    top_entry, score = hits[0]
    if score < threshold:
        return None
    answer = top_entry.content.strip()
    # Keep it concise and friendly; let FinalAnswerAgent handle ultimate tone elsewhere if needed
    return {
        "title": top_entry.title,
        "answer": answer,
        "source": "FAQ interne Tunisie (CNAM/assurances privées)"
    } 