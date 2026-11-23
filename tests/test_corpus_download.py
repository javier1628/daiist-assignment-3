"""The index stage fetches the corpus itself, and only the files it lacks."""

import pytest

from index import DOCUMENTS, ensure_corpus

NORMA_URL = "https://aduanas.gob.do/media/as3hx2ml/norma-general-01-2023-ajuste-tasas-por-servicios.pdf"


def put_all_but_the_norma(folder) -> None:
    for filename in DOCUMENTS:
        if filename != "norma-01-2023.pdf":
            (folder / filename).write_bytes(b"%PDF-1.7 already here")


def test_files_already_in_the_folder_are_not_downloaded_again(tmp_path):
    for filename in DOCUMENTS:
        (tmp_path / filename).write_bytes(b"%PDF-1.7 already here")

    def fetch(url: str) -> bytes:
        raise AssertionError(f"unexpected download of {url}")

    ensure_corpus(tmp_path, fetch=fetch)

    assert (tmp_path / "ley-168-21.pdf").read_bytes() == b"%PDF-1.7 already here"


def test_a_missing_file_is_downloaded_from_its_own_url_and_saved(tmp_path):
    put_all_but_the_norma(tmp_path)
    requested = []

    def fetch(url: str) -> bytes:
        requested.append(url)
        return b"%PDF-1.7 fresh copy"

    ensure_corpus(tmp_path, fetch=fetch)

    assert requested == [NORMA_URL]
    assert (tmp_path / "norma-01-2023.pdf").read_bytes() == b"%PDF-1.7 fresh copy"


def test_a_download_that_is_not_a_pdf_is_an_error_and_leaves_no_file_behind(tmp_path):
    put_all_but_the_norma(tmp_path)

    with pytest.raises(ValueError, match="not a PDF"):
        ensure_corpus(tmp_path, fetch=lambda url: b"<html>Access denied</html>")

    assert not (tmp_path / "norma-01-2023.pdf").exists()


def test_the_folder_is_created_when_it_does_not_exist(tmp_path):
    folder = tmp_path / "corpus"

    ensure_corpus(folder, fetch=lambda url: b"%PDF-1.7 fresh copy")

    assert sorted(path.name for path in folder.iterdir()) == sorted(DOCUMENTS)
