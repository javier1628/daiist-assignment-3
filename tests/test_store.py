"""From chunks to the saved search index. Vectors are made up here: no test calls the Gemini API."""

from embeddings import cache_key
from index import Chunk, embedded_text, heading, nearest, open_collection, store_chunks

TITULO = "TÍTULO II: DE ADUANAS Y EL CONTROL ADUANERO"
CAPITULO = "CAPÍTULO I: DEL TERRITORIO ADUANERO"


def chunk(number: int, part: int, text: str, source: str = "ley-168-21.pdf", **fields) -> Chunk:
    values = dict(title="Territorio aduanero", titulo=TITULO, capitulo=CAPITULO, seccion="", page=12)
    return Chunk(source=source, number=number, part=part, words=len(text.split()), text=text, **(values | fields))


def vectors_for(chunks_and_vectors: list[tuple[Chunk, list[float]]]) -> dict[str, list[float]]:
    """What the embedding cache would hold for these chunks."""
    return {cache_key(embedded_text(item)): vector for item, vector in chunks_and_vectors}


FIVE = chunk(5, 1, "Artículo 5.- Territorio aduanero. El territorio aduanero es todo el territorio nacional.")
SIX_A = chunk(6, 1, "Artículo 6.- Zona de jurisdicción aduanera.", title="Zona de jurisdicción aduanera")
SIX_B = chunk(6, 2, "Párrafo: La zona secundaria es el resto.", title="Zona de jurisdicción aduanera")
DECREE = chunk(
    6, 1, "ARTÍCULO 6. Los agentes deben renovar su licencia.", source="decreto-609-24.pdf",
    title="", titulo="", capitulo="", page=4,
)
VECTORS = vectors_for([(FIVE, [1.0, 0.0, 0.0]), (SIX_A, [0.0, 1.0, 0.0]), (SIX_B, [0.0, 0.0, 1.0]), (DECREE, [1.0, 1.0, 0.0])])


def test_the_heading_names_the_document_the_article_its_title_and_the_headings_above_it():
    assert heading(FIVE) == f"Ley 168-21 de Aduanas — Artículo 5 — Territorio aduanero — {TITULO} / {CAPITULO}"


def test_the_heading_leaves_out_what_the_article_does_not_have():
    assert heading(DECREE) == (
        "Decreto 609-24, Reglamento de aplicación del Título III de la Ley 168-21 de Aduanas — Artículo 6"
    )


def test_the_embedded_text_is_the_heading_as_title_and_then_the_chunk_text():
    assert embedded_text(SIX_B) == (
        f"title: Ley 168-21 de Aduanas — Artículo 6 — Zona de jurisdicción aduanera — {TITULO} / {CAPITULO}"
        " | text: Párrafo: La zona secundaria es el resto."
    )


def test_stored_chunks_are_read_back_from_disk_with_their_text_and_metadata(tmp_path):
    written, deleted = store_chunks(open_collection(tmp_path, create=True), [FIVE, SIX_A, SIX_B], VECTORS)

    saved = open_collection(tmp_path)  # a fresh open: only the files on disk, no embedder anywhere
    record = saved.get(ids=["ley-168-21.pdf#6#2"], include=["documents", "metadatas", "embeddings"])

    assert (written, deleted) == (3, 0)
    assert saved.count() == 3
    assert record["documents"] == ["Párrafo: La zona secundaria es el resto."]
    assert record["metadatas"] == [
        {
            "source": "ley-168-21.pdf",
            "article": 6,
            "part": 2,
            "title": "Zona de jurisdicción aduanera",
            "path": f"{TITULO} / {CAPITULO}",
            "page": 12,
            "embedded_text": embedded_text(SIX_B),
            "embedding_key": cache_key(embedded_text(SIX_B)),
        }
    ]
    assert record["embeddings"][0].tolist() == [0.0, 0.0, 1.0]


def test_storing_the_same_chunks_again_writes_nothing(tmp_path):
    store_chunks(open_collection(tmp_path, create=True), [FIVE, SIX_A, DECREE], VECTORS)

    again = store_chunks(open_collection(tmp_path), [FIVE, SIX_A, DECREE], VECTORS)

    assert again == (0, 0)
    assert open_collection(tmp_path).count() == 3


def test_a_chunk_its_document_no_longer_produces_is_deleted_and_a_changed_one_rewritten(tmp_path):
    store_chunks(open_collection(tmp_path, create=True), [FIVE, SIX_A, SIX_B], VECTORS)
    reworded = chunk(5, 1, "Artículo 5.- Territorio aduanero. Texto corregido.")
    vectors = VECTORS | vectors_for([(reworded, [0.5, 0.5, 0.0])])

    result = store_chunks(open_collection(tmp_path), [reworded, SIX_A], vectors)

    saved = open_collection(tmp_path)
    assert result == (1, 1)
    assert sorted(saved.get()["ids"]) == ["ley-168-21.pdf#5#1", "ley-168-21.pdf#6#1"]
    assert saved.get(ids=["ley-168-21.pdf#5#1"])["documents"] == ["Artículo 5.- Territorio aduanero. Texto corregido."]


def test_chunks_of_other_documents_are_left_alone(tmp_path):
    store_chunks(open_collection(tmp_path, create=True), [FIVE, DECREE], VECTORS)

    result = store_chunks(open_collection(tmp_path), [SIX_A], VECTORS)  # the law again, without its article 5

    assert result == (1, 1)
    assert sorted(open_collection(tmp_path).get()["ids"]) == ["decreto-609-24.pdf#6#1", "ley-168-21.pdf#6#1"]


def test_nearest_returns_the_closest_chunks_first_with_what_a_citation_needs(tmp_path):
    store_chunks(open_collection(tmp_path, create=True), [FIVE, SIX_A, SIX_B], VECTORS)

    results = nearest(open_collection(tmp_path), [0.1, 0.9, 0.2], k=2)

    assert [result["id"] for result in results] == ["ley-168-21.pdf#6#1", "ley-168-21.pdf#6#2"]
    assert results[0]["text"] == "Artículo 6.- Zona de jurisdicción aduanera."
    assert (results[0]["source"], results[0]["article"], results[0]["part"], results[0]["page"]) == (
        "ley-168-21.pdf", 6, 1, 12,
    )
    assert results[0]["distance"] < results[1]["distance"]
