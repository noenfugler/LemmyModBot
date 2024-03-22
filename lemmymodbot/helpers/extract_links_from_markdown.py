from typing import List

from mistletoe import Document
from mistletoe.span_token import Image, Link, AutoLink
from mistletoe.token import Token


def extract_links_from_markdown(markdown: str) -> List[str]:
    doc = Document(markdown)
    return _internal_extract_links_from_markdown(doc)


def _internal_extract_links_from_markdown(token: Token) -> List[str]:
    if isinstance(token, Image):
        return [token.src]
    if isinstance(token, Link) or isinstance(token, AutoLink):
        return [token.target]

    if "children" in vars(token):
        out = []
        for child in token.children:
            out += _internal_extract_links_from_markdown(child)
        return out

    return []
