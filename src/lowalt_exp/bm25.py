import math
from collections import Counter, defaultdict
from typing import Iterable, List, Tuple

from .tokenizer import char_ngrams


class BM25:
    def __init__(self, docs: List[str], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.doc_tokens = [char_ngrams(d) for d in docs]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.tf = [Counter(t) for t in self.doc_tokens]
        df = defaultdict(int)
        for toks in self.doc_tokens:
            for tok in set(toks):
                df[tok] += 1
        n_docs = len(docs)
        self.idf = {tok: math.log(1 + (n_docs - f + 0.5) / (f + 0.5)) for tok, f in df.items()}

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        q_tokens = char_ngrams(query)
        scores = []
        for i, tf in enumerate(self.tf):
            score = 0.0
            dl = self.doc_len[i] or 1
            for tok in q_tokens:
                if tok not in tf:
                    continue
                freq = tf[tok]
                idf = self.idf.get(tok, 0.0)
                denom = freq + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
                score += idf * (freq * (self.k1 + 1)) / denom
            if score > 0:
                scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
