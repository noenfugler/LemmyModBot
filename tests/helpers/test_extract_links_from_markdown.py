import unittest
from lemmymodbot import extract_links_from_markdown


class TestToxicityProcessor(unittest.TestCase):

    def test_extract_links_from_markdown_no_links(self):
        markdown = "This is a test without any links."
        links = extract_links_from_markdown(markdown)
        self.assertEqual(links, [])

    def test_extract_links_from_markdown_with_links(self):
        markdown = "This is a [test link](https://example.com)."
        links = extract_links_from_markdown(markdown)
        self.assertEqual(["https://example.com"], links)

    def test_extract_links_from_markdown_with_autolinks(self):
        markdown = "This is a <https://example.com>."
        links = extract_links_from_markdown(markdown)
        self.assertEqual(["https://example.com"], links)

    def test_extract_links_from_markdown_with_images(self):
        markdown = "This is a ![alt](https://example.com)."
        links = extract_links_from_markdown(markdown)
        self.assertEqual(["https://example.com"], links)

    def test_extract_links_from_markdown_with_links_in_list(self):
        markdown = "This is a\n\n* [test link](https://example.com)."
        links = extract_links_from_markdown(markdown)
        self.assertEqual(["https://example.com"], links)


if __name__ == '__main__':
    unittest.main()