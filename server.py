"""
Assignment 3: MCP server. Your editor and agent.py start it; by hand: `uv run server.py`.

- search(query): returns the top chunks, each with a citation and its text.
- add_document(path): runs a PDF through index.py's pipeline, embeds what has
  no saved vector yet and stores it.

The saved index is loaded at startup, from a temporary copy, and the corpus is
never re-embedded. A question reaches the embedding API only the first time
it is asked. Nothing is printed to stdout (it carries the protocol); progress
goes to stderr.

How chunks are ranked and how many are returned is one setting,
retrieval.DEFAULT_SETTING, which the CORPUS_RETRIEVAL environment variable
overrides ("vector:5", "hybrid:5").
"""

import functools
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import embeddings
import index
import retrieval

mcp = MCPServer("corpus", log_level="WARNING")


@functools.cache
def retriever() -> retrieval.Retriever:
    """The chunks of the saved index, loaded once."""
    return retrieval.Retriever(index.open_snapshot())


def describe(result: index.AddResult) -> str:
    """What add_document did, in words."""
    if result.stopped:
        return (
            f"{result.source} was NOT indexed: the embedding service refused ({result.stopped}). "
            f"{result.sent} texts were embedded and saved before that, so calling again later sends only the rest. "
            "The index was not changed."
        )
    if not result.added and not result.removed:
        return (
            f"{result.source} is already indexed and unchanged ({result.chunks} chunks). "
            "Nothing was sent to the embedding service."
        )
    return (
        f"{result.source} indexed: {result.added} chunks added, {result.removed} removed, "
        f"{result.unchanged} left unchanged. It now has {result.chunks} chunks. "
        f"{result.sent} texts were sent to the embedding service."
    )


@mcp.tool()
def search(query: str) -> str:
    """Search the customs legislation of the Dominican Republic and return the passages closest to a question.

    The corpus is in Spanish and split by article: the customs law (Ley 168-21 de Aduanas), its general
    regulation (Decreto 755-22) and the regulation on customs operators (Decreto 609-24), plus any document
    added with add_document. Use it for every question about Dominican customs rules, such as duties and
    their basis, declarations, customs regimes, deadlines, agents and operators, offences and penalties.
    Write the query in Spanish, as a full question or as key terms.

    Returns the best passages, best first. Each one starts with a citation line: the tag to cite the passage by,
    such as [Ley 168-21, art. 80], then the document, the article, the article's title, which part of the article
    the passage is, the page the article starts on and the file name. The text of the passage follows. The text
    comes from scanned documents, so it has occasional stray characters. If none of the passages answers the
    question, the corpus does not cover it.
    """
    try:
        vector = embeddings.embed_query(query, index.QUERY_EMBEDDINGS_FILE, embeddings.gemini_embedder())
    except embeddings.QuotaStop as stop:  # reported with its reason, so the model can say why there is no answer
        raise ToolError(f"The question could not be embedded, so nothing was searched: {stop}") from stop
    return retrieval.format_results(retriever().search(query, vector, retrieval.current_setting()))


@mcp.tool()
def add_document(path: str) -> str:
    """Add a PDF to the corpus so that search can find it, or update a document whose file changed.

    `path` is the path of a PDF on this machine whose text is organised in numbered articles
    (Artículo 1, Artículo 2...). The file is cleaned, split by article, cut into chunks, embedded and stored.

    Returns what was done. A file that is already indexed with the same content is skipped and nothing is sent
    to the embedding service. A file with the same name as an indexed document but different content replaces
    that document's chunks, and the answer says how many were removed and added.
    """
    try:
        result = index.add_document(Path(path).expanduser(), index.open_collection(), embeddings.gemini_embedder())
    except (FileNotFoundError, ValueError) as error:  # no such file, not a PDF, or no articles found in it
        raise ToolError(f"The document was not added: {error}") from error
    if result.added or result.removed:
        retriever.cache_clear()  # the next search loads the index again, with the new chunks
    return describe(result)


if __name__ == "__main__":
    retriever()  # load the index before the first request
    mcp.run()  # stdio
