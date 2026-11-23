"""The calculations in scripts/describe_corpus.py that are not plain counting."""

import pytest

from describe_corpus import chunk_stats, percentile
from index import Article


def article(number: int, *lines: str) -> Article:
    text = "\n".join(lines)
    return Article(
        source="decreto-755-22.pdf", number=number, title="", titulo="", capitulo="", seccion="",
        page=1, words=len(text.split()), text=text,
    )


def test_chunk_stats_counts_chunks_split_articles_and_chunks_still_over_the_limit():
    short = article(1, "Artículo 1.- Objeto. Regular el tránsito.")  # 6 words: one chunk
    cut_in_two = article(  # 17 words: chunks of 9 and 8
        2,
        "Artículo 2.- Plazo. El plazo es de treinta días.",
        "Párrafo I.- El plazo puede prorrogarse una vez.",
    )
    no_boundary = article(  # 14 words and nowhere to cut
        3, "Artículo 3.- Alcance. Esta disposición rige en todo el territorio nacional sin excepción alguna."
    )

    stats = chunk_stats([short, cut_in_two, no_boundary], 10)

    assert stats["chunks"] == 4
    assert stats["articles_split"] == 1
    assert stats["median"] == 8.5  # of 6, 8, 9 and 14
    assert stats["max"] == 14
    assert [(chunk.number, chunk.words) for chunk in stats["over"]] == [(3, 14)]


@pytest.mark.parametrize(
    ("values", "fraction", "expected"),
    [
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.9, 9),  # nine of the ten values are at or below 9
        ([10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 0.9, 9),  # order of the input does not matter
        ([1, 2, 3, 4], 0.9, 4),
        ([11, 73, 4292], 0.9, 4292),
        ([5], 0.9, 5),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.5, 5),
    ],
)
def test_percentile_is_the_smallest_value_with_that_share_of_values_at_or_below_it(values, fraction, expected):
    assert percentile(values, fraction) == expected
