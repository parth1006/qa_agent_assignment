"""
Utils Package

This package contains utility modules:
- DocumentParser: Multi-format document parsing
- TextChunker: Text splitting with metadata
- HTMLAnalyzer: HTML structure extraction

"""

from backend.utils.document_parser import DocumentParser, get_document_parser
from backend.utils.chunking import TextChunker, get_text_chunker
from backend.utils.html_analyzer import HTMLAnalyzer, analyze_html_file

__all__ = [
    "DocumentParser",
    "get_document_parser",
    "TextChunker",
    "get_text_chunker",
    "HTMLAnalyzer",
    "analyze_html_file",
]