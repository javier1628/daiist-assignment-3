"""Keyword ranking, rank fusion and the retrieval setting. Vectors are made up: no test calls the Gemini API."""

import pytest

from embeddings import cache_key
from index import Chunk, embedded_text, open_collection, store_chunks
from retrieval import BM25, Retriever, Setting, format_results, fuse, read_setting, tokens


def chunk(number: int, text: str, title: str, source: str = "ley-168-21.pdf") -> Chunk:
    return Chunk(
        source=source, number=number, title=title, titulo="", capitulo="", seccion="",
        part=1, page=10 + number, words=len(text.split()), text=text,
    )


VALOR = chunk(80, "Artículo 80.- La base imponible es el valor en aduana de las mercancías.", "Base imponible")
SUBASTA = chunk(124, "Artículo 124.- El precio base de la subasta incluye los tributos.", "Precio base de la subasta")
ABANDONO = chunk(112, "Artículo 112.- Las mercancías en abandono pasan a subasta pública.", "Abandono")


@pytest.fixture
def retriever(tmp_path) -> Retriever:
    collection = open_collection(tmp_path, create=True)
    vectors = {
        cache_key(embedded_text(item)): vector
        for item, vector in ((VALOR, [1.0, 0.0, 0.0]), (SUBASTA, [0.0, 1.0, 0.0]), (ABANDONO, [0.0, 0.0, 1.0]))
    }
    store_chunks(collection, [VALOR, SUBASTA, ABANDONO], vectors)
    return Retriever(collection)


def test_tokens_are_lower_case_stems_without_accents_or_stop_words():
    assert tokens("¿Sobre qué VALOR se calculan los impuestos de importación?") == [
        "valor", "calcul", "impuest", "import",
    ]


def test_tokens_keep_numbers_and_drop_single_letters():
    assert tokens("Ley 168-21, artículo 5, literal b)") == ["ley", "168", "21", "articul", "5", "literal"]


def test_forms_of_the_same_word_give_the_same_token():
    assert tokens("calculan") == tokens("cálculo") == tokens("calcular") == ["calcul"]
    assert tokens("impuestos") == tokens("impuesto")
    assert tokens("importaciones") == tokens("importación") == tokens("IMPORTACION")
    assert tokens("garantías") == tokens("garantía")


def test_a_word_gives_the_same_token_with_or_without_its_accents():
    assert tokens("garantia") == tokens("garantía") == tokens("GARANTÍA")
    assert tokens("regimen aduanero") == tokens("régimen aduanero")
    assert tokens("articulo") == tokens("artículo")
    assert tokens("garantías") == tokens("garantia")  # and the plural still joins them


def test_tokens_stay_plain_ascii_after_stemming():
    found = tokens("Los AÑOS de la compañía, la señalización pública y el güiro")

    assert found and all(token.isascii() and token.isalnum() for token in found)
    assert tokens("AÑOS") == tokens("años")


def test_bm25_ranks_the_document_with_the_rarer_query_word_first_and_leaves_out_those_with_none():
    documents = [
        tokens("las mercancías en abandono pasan a subasta"),
        tokens("la base imponible es el valor en aduana de las mercancías"),
        tokens("el oficial de aduanas firma el acta"),
    ]

    ranking = BM25(documents).rank(tokens("valor de las mercancías"))

    assert ranking == [1, 0]  # document 1 has both words; document 0 only the common one; document 2 has neither


def test_bm25_prefers_the_shorter_of_two_documents_that_match_equally():
    documents = [tokens("subasta pública de mercancías abandonadas y decomisadas en puerto"), tokens("subasta pública")]

    assert BM25(documents).rank(tokens("subasta")) == [1, 0]


def test_fusion_adds_one_over_sixty_plus_rank_from_each_ranking():
    # a: 1/61 + 1/62, c: 1/63 + 1/61, b: 1/62, d: 1/63
    assert fuse([["a", "b", "c"], ["c", "a", "d"]]) == ["a", "c", "b", "d"]


def test_the_setting_is_a_mode_and_a_k_and_defaults_to_vector_with_five():
    assert read_setting(None) == Setting("vector", 5)
    assert read_setting("hybrid:3") == Setting("hybrid", 3)


@pytest.mark.parametrize("value", ["fuzzy:5", "vector", "vector:0", "hybrid:five", ""])
def test_a_setting_that_is_not_a_known_mode_and_a_positive_k_is_an_error(value):
    with pytest.raises(ValueError, match="CORPUS_RETRIEVAL"):
        read_setting(value)


def test_vector_mode_returns_the_chunks_nearest_to_the_question_vector(retriever):
    results = retriever.search("¿qué pasa con la subasta?", [0.9, 0.4, 0.1], Setting("vector", 2))

    assert [(result["article"], result["title"]) for result in results] == [(80, "Base imponible"), (124, "Precio base de la subasta")]
    assert results[0]["text"] == VALOR.text


def test_hybrid_mode_moves_up_a_chunk_that_also_matches_the_words_of_the_question(retriever):
    # By vector: 80, 124, 112. By keywords ("subasta", "publica"): 112, 124.
    # Fused: 112 (1/63 + 1/61), then 124 (1/62 + 1/62), then 80 (1/61).
    results = retriever.search("¿qué pasa con la subasta pública?", [0.9, 0.4, 0.1], Setting("hybrid", 3))

    assert [result["article"] for result in results] == [112, 124, 80]


def test_results_are_shown_as_a_numbered_citation_followed_by_the_text(retriever):
    results = retriever.search("subasta", [0.0, 1.0, 0.0], Setting("vector", 1))

    assert format_results(results) == (
        "[1] Ley 168-21 de Aduanas — Artículo 124 — Precio base de la subasta — part 1 — page 134 — ley-168-21.pdf\n"
        "Artículo 124.- El precio base de la subasta incluye los tributos."
    )


def test_keywords_match_whichever_side_lost_its_accents(tmp_path):
    accented = chunk(42, "Artículo 42.- Los agentes deberán depositar una garantía.", "Rendición de garantía")
    plain = chunk(43, "ARTICULO 43. La garantia se hara efectiva.", "")
    other = chunk(44, "Artículo 44.- El plazo es de treinta días.", "Plazo")
    collection = open_collection(tmp_path, create=True)
    vectors = {cache_key(embedded_text(item)): [1.0, 0.0, 0.0] for item in (accented, plain, other)}
    store_chunks(collection, [accented, plain, other], vectors)
    found = Retriever(collection)

    assert set(found.by_keywords("garantia", 5)) == {"ley-168-21.pdf#42#1", "ley-168-21.pdf#43#1"}
    assert set(found.by_keywords("garantía", 5)) == {"ley-168-21.pdf#42#1", "ley-168-21.pdf#43#1"}


def test_the_vector_ranking_is_exact_and_chunks_that_tie_come_in_the_order_of_their_ids(tmp_path):
    first = chunk(7, "Artículo 7.- Uno.", "Uno")
    twin = chunk(3, "Artículo 3.- Otro con el mismo vector.", "Otro")
    far = chunk(9, "Artículo 9.- Lejos.", "Lejos")
    collection = open_collection(tmp_path, create=True)
    vectors = {
        cache_key(embedded_text(first)): [1.0, 0.0, 0.0],
        cache_key(embedded_text(twin)): [2.0, 0.0, 0.0],  # same direction as the first, another length
        cache_key(embedded_text(far)): [0.0, 0.0, 1.0],
    }
    store_chunks(collection, [first, twin, far], vectors)  # stored 7, 3, 9: the tie is not settled by that order

    ranking = Retriever(collection).by_vector([0.9, 0.0, 0.1], 3)

    assert ranking == ["ley-168-21.pdf#3#1", "ley-168-21.pdf#7#1", "ley-168-21.pdf#9#1"]
