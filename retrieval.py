"""
Retrieval over the saved search index: by vector alone, or by vector and
keywords fused. server.py and evaluate.py both use it.

Nothing in this file calls the API: the vector of the question is passed in,
and the keyword side is computed here from the stored chunk texts.

Chunks are ranked by exact cosine similarity over the vectors read from the
index, not by ChromaDB's own search. That search is approximate and rebuilt
on every load, so the same question could get a different ranking on each run.
"""

import functools
import math
import os
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import snowballstemmer

import index

# The one retrieval setting: "<mode>:<k>". The mode is how chunks are ranked
# (vector, or hybrid = vector and keywords fused) and k how many are returned.
# Set the CORPUS_RETRIEVAL environment variable to override it for one run.
DEFAULT_SETTING = "vector:5"
SETTING_VARIABLE = "CORPUS_RETRIEVAL"

CANDIDATES = 50  # how deep each ranking goes before the two are fused
RRF_K = 60  # the usual constant of reciprocal rank fusion
BM25_K1, BM25_B = 1.5, 0.75  # the usual BM25 settings

# "calculan", "calculo" and "calcular" all become "calcul". Stems are remembered: the corpus repeats its words.
stem = functools.lru_cache(maxsize=None)(snowballstemmer.stemmer("spanish").stemWord)

# Spanish words that say nothing about the topic, written without accents.
STOP_WORDS = frozenset(
    """
    a al algo alguna algunas alguno algunos ante antes aquel aquella aquellas aquellos asi aun aunque cada como con
    contra cual cuales cuando de del desde donde durante e el ella ellas ello ellos en entre era eran es esa esas ese
    eso esos esta estan estas este esto estos fue fueron ha han hasta hay la las le les lo los mas me mi mientras muy
    ni no nos o os otra otras otro otros para pero por porque que quien quienes se sea sean segun ser si sido sin
    sobre son su sus tambien tanto te tiene tienen toda todas todo todos tu tus u un una unas uno unos y ya
    """.split()
)


@dataclass(frozen=True)
class Setting:
    mode: str  # "vector" or "hybrid"
    k: int  # chunks returned


def read_setting(value: str | None) -> Setting:
    """Parse a setting such as "hybrid:5". None means the default."""
    match = re.fullmatch(r"(vector|hybrid):([1-9]\d*)", (DEFAULT_SETTING if value is None else value).strip())
    if match is None:
        raise ValueError(
            f"{SETTING_VARIABLE} must be a mode and a number of chunks, such as vector:5 or hybrid:5, not {value!r}."
        )
    return Setting(match.group(1), int(match.group(2)))


def current_setting() -> Setting:
    """The setting in force: the environment variable if it is set, the default otherwise."""
    return read_setting(os.environ.get(SETTING_VARIABLE))


def fold(text: str) -> str:
    """The text without accents or other marks: "pública" -> "publica", "años" -> "anos"."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def tokens(text: str) -> list[str]:
    """Words for keyword search: lower case, accents folded, stop words and single letters dropped, stemmed.

    Chunks and questions both go through here. Accents are folded before
    stemming, so a word matches whether or not either side wrote its accents:
    "garantia", "garantía" and "garantías" all become "garanti".
    """
    return [
        stem(word)
        for word in re.findall(r"[a-z0-9]+", fold(text.lower()))
        if word not in STOP_WORDS and (len(word) > 1 or word.isdigit())
    ]


class BM25:
    """Okapi BM25 over documents given as lists of tokens."""

    def __init__(self, documents: list[list[str]]):
        self.frequencies = [Counter(document) for document in documents]
        self.lengths = [len(document) for document in documents]
        self.average_length = sum(self.lengths) / len(documents)
        containing = Counter(token for frequencies in self.frequencies for token in frequencies)
        self.idf = {
            token: math.log(1 + (len(documents) - count + 0.5) / (count + 0.5)) for token, count in containing.items()
        }

    def score(self, query: list[str], position: int) -> float:
        frequencies = self.frequencies[position]
        norm = BM25_K1 * (1 - BM25_B + BM25_B * self.lengths[position] / self.average_length)
        return sum(
            self.idf[token] * frequencies[token] * (BM25_K1 + 1) / (frequencies[token] + norm)
            for token in set(query)
            if token in frequencies
        )

    def rank(self, query: list[str]) -> list[int]:
        """Positions of the documents that share a token with the query, best first."""
        scores = [(self.score(query, position), position) for position in range(len(self.lengths))]
        return [position for score, position in sorted(scores, key=lambda item: (-item[0], item[1])) if score > 0]


def fuse(rankings: list[list[str]]) -> list[str]:
    """Reciprocal rank fusion: each ranking gives an item 1 / (RRF_K + its rank); the sums decide the order."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item] = scores.get(item, 0.0) + 1 / (RRF_K + rank)
    return sorted(scores, key=lambda item: -scores[item])  # ties keep the order of the first ranking


class Retriever:
    """The chunks of a saved index, ready to be ranked for a question."""

    def __init__(self, collection):
        stored = collection.get(include=["documents", "metadatas", "embeddings"])
        # Sorted by id, so that ties are settled the same way whatever order the store returns its chunks in.
        order = sorted(range(len(stored["ids"])), key=lambda position: stored["ids"][position])
        self.ids = [stored["ids"][position] for position in order]
        self.records = {
            stored["ids"][position]: {
                "id": stored["ids"][position],
                "text": stored["documents"][position],
                **stored["metadatas"][position],
            }
            for position in order
        }
        vectors = np.asarray([stored["embeddings"][position] for position in order], dtype=np.float64)
        self.vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)  # unit length: a dot product is the cosine
        # Keywords are matched against the same text the vectors were made from: heading and chunk.
        self.bm25 = BM25([tokens(self.records[chunk_id]["embedded_text"]) for chunk_id in self.ids])

    def by_vector(self, vector: Sequence[float], count: int) -> list[str]:
        """The chunks most similar to a vector by exact cosine similarity, best first."""
        question = np.asarray(vector, dtype=np.float64)
        similarity = self.vectors @ (question / np.linalg.norm(question))
        return [self.ids[position] for position in np.argsort(-similarity, kind="stable")[:count]]

    def by_keywords(self, question: str, count: int) -> list[str]:
        return [self.ids[position] for position in self.bm25.rank(tokens(question))[:count]]

    def search(self, question: str, vector: Sequence[float], setting: Setting) -> list[dict]:
        """The setting's k best chunks for a question whose vector is given, best first."""
        if setting.mode == "vector":
            ids = self.by_vector(vector, setting.k)
        else:
            ids = fuse([self.by_vector(vector, CANDIDATES), self.by_keywords(question, CANDIDATES)])[: setting.k]
        return [self.records[chunk_id] for chunk_id in ids]


def format_results(results: list[dict]) -> str:
    """Each chunk as a numbered citation line followed by its text."""
    return "\n\n".join(
        f"[{number}] {index.citation(result)}\n{result['text']}" for number, result in enumerate(results, 1)
    )
