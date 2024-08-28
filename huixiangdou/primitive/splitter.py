# Copyright (c) OpenMMLab. All rights reserved.
# modified from langchain
# 1. Use `Chunk` instead of `Document`
# 2. Default chunksize using 832
# 3. `MarkdownSplitter` support parsing URI (file or URI)
import copy
import os
import pdb
import json
import re
from abc import ABC, abstractmethod
from typing import (AbstractSet, Any, Callable, Collection, Dict, Iterable,
                    List, Literal, Optional, Sequence, Tuple, Type, TypedDict,
                    TypeVar, Union)

from loguru import logger

from .chunk import Chunk
from .file_operation import FileOperation


class LineType(TypedDict):
    """Line type as typed dict."""

    metadata: Dict[str, str]
    content: str


class HeaderType(TypedDict):
    """Header type as typed dict."""

    level: int
    name: str
    data: str


class TextSplitter(ABC):
    """Interface for splitting text into chunks."""

    def __init__(
        self,
        chunk_size: int = 832,
        chunk_overlap: int = 32,
        length_function: Callable[[str], int] = len,
        keep_separator: Union[bool, Literal['start', 'end']] = False,
        add_start_index: bool = False,
        strip_whitespace: bool = True,
    ) -> None:
        """Create a new TextSplitter.

        Args:
            chunk_size: Maximum size of chunks to return
            chunk_overlap: Overlap in characters between chunks
            length_function: Function that measures the length of given chunks
            keep_separator: Whether to keep the separator and where to place it
                            in each corresponding chunk (True='start')
            add_start_index: If `True`, includes chunk's start index in metadata
            strip_whitespace: If `True`, strips whitespace from the start and end of
                              every chunk
        """
        if chunk_overlap > chunk_size:
            raise ValueError(
                f'Got a larger chunk overlap ({chunk_overlap}) than chunk size '
                f'({chunk_size}), should be smaller.')
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        self._keep_separator = keep_separator
        self._add_start_index = add_start_index
        self._strip_whitespace = strip_whitespace

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """Split text into multiple components."""

    def create_chunks(self,
                      texts: List[str],
                      metadatas: Optional[List[dict]] = None) -> List[Chunk]:
        """Create chunks from a list of texts."""
        _metadatas = metadatas or [{}] * len(texts)
        chunks = []
        for i, text in enumerate(texts):
            index = 0
            previous_chunk_len = 0
            for chunk in self.split_text(text):
                metadata = copy.deepcopy(_metadatas[i])
                if self._add_start_index:
                    offset = index + previous_chunk_len - self._chunk_overlap
                    index = text.find(chunk, max(0, offset))
                    metadata['start_index'] = index
                    previous_chunk_len = len(chunk)
                new_chunk = Chunk(content_or_path=chunk, metadata=metadata)
                chunks.append(new_chunk)
        return chunks

    def _join_chunks(self, chunks: List[str], separator: str) -> Optional[str]:
        text = separator.join(chunks)
        if self._strip_whitespace:
            text = text.strip()
        if text == '':
            return None
        else:
            return text

    def _merge_splits(self, splits: Iterable[str],
                      separator: str) -> List[str]:
        # We now want to combine these smaller pieces into medium size
        # chunks to send to the LLM.
        separator_len = self._length_function(separator)

        chunks = []
        current_chunk: List[str] = []
        total = 0
        for d in splits:
            _len = self._length_function(d)
            if (total + _len + (separator_len if len(current_chunk) > 0 else 0)
                    > self._chunk_size):
                if total > self._chunk_size:
                    logger.warning(
                        f'Created a chunk of size {total}, '
                        f'which is longer than the specified {self._chunk_size}'
                    )
                if len(current_chunk) > 0:
                    chunk = self._join_chunks(current_chunk, separator)
                    if chunk is not None:
                        chunks.append(chunk)
                    # Keep on popping if:
                    # - we have a larger chunk than in the chunk overlap
                    # - or if we still have any chunks and the length is long
                    while total > self._chunk_overlap or (
                            total + _len +
                        (separator_len if len(current_chunk) > 0 else 0) >
                            self._chunk_size and total > 0):
                        total -= self._length_function(current_chunk[0]) + (
                            separator_len if len(current_chunk) > 1 else 0)
                        current_chunk = current_chunk[1:]
            current_chunk.append(d)
            total += _len + (separator_len if len(current_chunk) > 1 else 0)
        chunk = self._join_chunks(current_chunk, separator)
        if chunk is not None:
            chunks.append(chunk)
        return chunks


def _split_text_with_regex(
        text: str, separator: str,
        keep_separator: Union[bool, Literal['start', 'end']]) -> List[str]:
    # Now that we have the separator, split the text
    if separator:
        if keep_separator:
            # The parentheses in the pattern keep the delimiters in the result.
            _splits = re.split(f'({separator})', text)
            splits = (([
                _splits[i] + _splits[i + 1]
                for i in range(0,
                               len(_splits) - 1, 2)
            ]) if keep_separator == 'end' else ([
                _splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)
            ]))
            if len(_splits) % 2 == 0:
                splits += _splits[-1:]
            splits = ((splits + [_splits[-1]]) if keep_separator == 'end' else
                      ([_splits[0]] + splits))
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s != '']


class CharacterTextSplitter(TextSplitter):
    """Splitting text that looks at characters."""

    def __init__(self,
                 separator: str = '\n\n',
                 is_separator_regex: bool = False,
                 **kwargs: Any) -> None:
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator
        self._is_separator_regex = is_separator_regex

    def split_text(self, text: str) -> List[str]:
        """Split incoming text and return chunks."""
        # First we naively split the large input into a bunch of smaller ones.
        separator = (self._separator if self._is_separator_regex else
                     re.escape(self._separator))
        splits = _split_text_with_regex(text, separator, self._keep_separator)
        _separator = '' if self._keep_separator else self._separator
        return self._merge_splits(splits, _separator)


class RecursiveCharacterTextSplitter(TextSplitter):
    """Splitting text by recursively look at characters.

    Recursively tries to split by different characters to find one that works.
    """

    def __init__(
        self,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        is_separator_regex: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(keep_separator=keep_separator, **kwargs)
        self._separators = separators or ['\n\n', '\n', ' ', '']
        self._is_separator_regex = is_separator_regex

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self._is_separator_regex else re.escape(_s)
            if _s == '':
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1:]
                break

        _separator = separator if self._is_separator_regex else re.escape(
            separator)
        splits = _split_text_with_regex(text, _separator, self._keep_separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        _separator = '' if self._keep_separator else separator
        for s in splits:
            if self._length_function(s) < self._chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return final_chunks

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self._separators)


# modified from https://github.com/chatchat-space/Langchain-Chatchat/blob/master/text_splitter/chinese_recursive_text_splitter.py
class ChineseRecursiveTextSplitter(RecursiveCharacterTextSplitter):

    def __init__(
        self,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        is_separator_regex: bool = True,
        **kwargs: Any,
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(keep_separator=keep_separator, **kwargs)
        self._separators = separators or [
            '\n\n', '\n', '。|！|？', '\.\s|\!\s|\?\s', '；|;\s', '，|,\s'
        ]
        self._is_separator_regex = is_separator_regex

    def _split_text_with_regex_from_end(self, text: str, separator: str,
                                        keep_separator: bool) -> List[str]:
        # Now that we have the separator, split the text
        if separator:
            if keep_separator:
                # The parentheses in the pattern keep the delimiters in the result.
                _splits = re.split(f'({separator})', text)
                splits = [
                    ''.join(i) for i in zip(_splits[0::2], _splits[1::2])
                ]
                if len(_splits) % 2 == 1:
                    splits += _splits[-1:]
                # splits = [_splits[0]] + splits
            else:
                splits = re.split(separator, text)
        else:
            splits = list(text)
        return [s for s in splits if s != '']

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self._is_separator_regex else re.escape(_s)
            if _s == '':
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1:]
                break

        _separator = separator if self._is_separator_regex else re.escape(
            separator)
        splits = self._split_text_with_regex_from_end(text, _separator,
                                                      self._keep_separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        _separator = '' if self._keep_separator else separator
        for s in splits:
            if self._length_function(s) < self._chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return [
            re.sub(r'\n{2,}', '\n', chunk.strip()) for chunk in final_chunks
            if chunk.strip() != ''
        ]


class MarkdownTextRefSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along Markdown-formatted headings."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a MarkdownTextRefSplitter."""
        separators = [
            # First, try to split along Markdown headings (starting with level 2)
            '\n#{1,6} ',
            # Note the alternative syntax for headings (below) is not handled here
            # Heading level 2
            # ---------------
            # End of code block
            '```\n',
            # Horizontal lines
            '\n\\*\\*\\*+\n',
            '\n---+\n',
            '\n___+\n',
            # Note that this splitter doesn't handle horizontal lines defined
            # by *three or more* of ***, ---, or ___, but this is not handled
            '\n\n',
            '\n',
            ' ',
            ''
        ]
        super().__init__(separators=separators, **kwargs)


class MarkdownHeaderTextSplitter:
    """Splitting markdown files based on specified headers."""

    def __init__(
        self,
        headers_to_split_on: List[Tuple[str, str]] = [
            ('#', 'Header 1'),
            ('##', 'Header 2'),
            ('###', 'Header 3'),
        ],
        strip_headers: bool = True,
    ):
        """Create a new MarkdownHeaderTextSplitter.

        Args:
            headers_to_split_on: Headers we want to track
            strip_headers: Strip split headers from the content of the chunk
        """
        # Given the headers we want to split on,
        # (e.g., "#, ##, etc") order by length
        self.headers_to_split_on = sorted(
            headers_to_split_on, key=lambda split: len(split[0]), reverse=True
        )
        # Strip headers split headers from the content of the chunk
        self.strip_headers = strip_headers
        super().__init__()

    def aggregate_lines_to_chunks(self, lines: List[LineType],
                                  base_meta: dict) -> List[Chunk]:
        """Combine lines with common metadata into chunks
        Args:
            lines: Line of text / associated header metadata
        """
        aggregated_chunks: List[LineType] = []

        for line in lines:
            if (
                aggregated_chunks
                and aggregated_chunks[-1]["metadata"] == line["metadata"]
            ):

                # If the last line in the aggregated list
                # has the same metadata as the current line,
                # append the current content to the last lines's content
                aggregated_chunks[-1]["content"] += "  \n" + line["content"]
            elif (
                aggregated_chunks
                and aggregated_chunks[-1]["metadata"] != line["metadata"]
                # may be issues if other metadata is present
                and len(aggregated_chunks[-1]["metadata"]) < len(line["metadata"])
                and aggregated_chunks[-1]["content"].split("\n")[-1][0] == "#"
                and not self.strip_headers
            ):
                # If the last line in the aggregated list
                # has different metadata as the current line,
                # and has shallower header level than the current line,
                # and the last line is a header,
                # and we are not stripping headers,
                # append the current content to the last line's content
                aggregated_chunks[-1]["content"] += "  \n" + line["content"]
                # and update the last line's metadata
                aggregated_chunks[-1]["metadata"] = line["metadata"]

            else:
                # Otherwise, append the current line to the aggregated list
                aggregated_chunks.append(line)

        return [
            Chunk(content_or_path=chunk["content"],
                  metadata=dict(chunk['metadata'], **base_meta))
            for chunk in aggregated_chunks
        ]

    def create_chunks(self, text: str, metadata: dict = {}) -> List[Chunk]:
        """Split markdown file
        Args:
            text: Markdown file"""

        # Split the input text by newline character ("\n").
        lines = text.split("\n")
        # Final output
        lines_with_metadata: List[LineType] = []
        # Content and metadata of the chunk currently being processed
        current_content: List[str] = []
        current_metadata: Dict[str, str] = {}
        # Keep track of the nested header structure
        # header_stack: List[Dict[str, Union[int, str]]] = []
        header_stack: List[HeaderType] = []
        initial_metadata: Dict[str, str] = {}

        in_code_block = False
        opening_fence = ""

        for line in lines:
            stripped_line = line.strip()
            # Remove all non-printable characters from the string, keeping only visible
            # text.
            stripped_line = "".join(filter(str.isprintable, stripped_line))
            if not in_code_block:
                # Exclude inline code spans
                if stripped_line.startswith("```") and stripped_line.count("```") == 1:
                    in_code_block = True
                    opening_fence = "```"
                elif stripped_line.startswith("~~~"):
                    in_code_block = True
                    opening_fence = "~~~"
            else:
                if stripped_line.startswith(opening_fence):
                    in_code_block = False
                    opening_fence = ""

            if in_code_block:
                current_content.append(stripped_line)
                continue

            # Check each line against each of the header types (e.g., #, ##)
            for sep, name in self.headers_to_split_on:
                # Check if line starts with a header that we intend to split on
                if stripped_line.startswith(sep) and (
                    # Header with no text OR header is followed by space
                    # Both are valid conditions that sep is being used a header
                    len(stripped_line) == len(sep) or stripped_line[len(sep)] == " "
                ):
                    # Ensure we are tracking the header as metadata
                    if name is not None:
                        # Get the current header level
                        current_header_level = sep.count("#")

                        # Pop out headers of lower or same level from the stack
                        while (
                            header_stack
                            and header_stack[-1]["level"] >= current_header_level
                        ):
                            # We have encountered a new header
                            # at the same or higher level
                            popped_header = header_stack.pop()
                            # Clear the metadata for the
                            # popped header in initial_metadata
                            if popped_header["name"] in initial_metadata:
                                initial_metadata.pop(popped_header["name"])

                        # Push the current header to the stack
                        header: HeaderType = {
                            "level": current_header_level,
                            "name": name,
                            "data": stripped_line[len(sep) :].strip(),
                        }
                        header_stack.append(header)
                        # Update initial_metadata with the current header
                        initial_metadata[name] = header["data"]

                    # Add the previous line to the lines_with_metadata
                    # only if current_content is not empty
                    if current_content:
                        lines_with_metadata.append(
                            {
                                "content": "\n".join(current_content),
                                "metadata": current_metadata.copy(),
                            }
                        )
                        current_content.clear()

                    if not self.strip_headers:
                        current_content.append(stripped_line)

                    break
            else:
                if stripped_line:
                    current_content.append(stripped_line)
                elif current_content:
                    lines_with_metadata.append(
                        {
                            "content": "\n".join(current_content),
                            "metadata": current_metadata.copy(),
                        }
                    )
                    current_content.clear()

            current_metadata = initial_metadata.copy()

        if current_content:
            lines_with_metadata.append(
                {"content": "\n".join(current_content), "metadata": current_metadata}
            )

        # lines_with_metadata has each line with associated header metadata
        # aggregate these into chunks based on common metadata
        return self.aggregate_lines_to_chunks(lines_with_metadata,
                                              base_meta=metadata)

def nested_split_markdown(filepath: str,
                          text: str,
                          chunksize: int = 832,
                          metadata: dict = {}):
    """First split by header, then by length.

    `header` should be part of content.
    """
    head_splitter = MarkdownHeaderTextSplitter()
    chunks = head_splitter.create_chunks(text, metadata=metadata)
    text_chunks = []
    image_chunks = []

    text_ref_splitter = MarkdownTextRefSplitter(chunk_size=chunksize)
    md_image_pattern = re.compile(r'\[([^\]]+)\]\(([a-zA-Z0-9:/._~#-]+)?\)')
    html_image_pattern = re.compile(r'<img\s+[^>]*?src=["\']([^"\']*)["\'][^>]*>')
    file_opr = FileOperation()

    for chunk in chunks:
        header = ''
        if 'Header 1' in chunk.metadata:
            header += chunk.metadata['Header 1']
        if 'Header 2' in chunk.metadata:
            header += ' '
            header += chunk.metadata['Header 2']
        if 'Header 3' in chunk.metadata:
            header += ' '
            header += chunk.metadata['Header 3']

        if len(chunk.content_or_path) > chunksize:
            subchunks = text_ref_splitter.create_chunks([chunk.content_or_path], [chunk.metadata])

            for subchunk in subchunks:
                if len(subchunk.content_or_path) >= 10:
                    subchunk.content_or_path = '{} {}'.format(header, subchunk.content_or_path.lower())
                    text_chunks.append(subchunk)
            
        elif len(chunk.content_or_path) >= 10:
            content = '{} {}'.format(header, chunk.content_or_path.lower())
            text_chunks.append(Chunk(content, metadata))
    
        # extract images path
        dirname = os.path.dirname(filepath)

        image_paths = []
        for match in md_image_pattern.findall(chunk.content_or_path):
            image_paths.append(match[1])
        for match in html_image_pattern.findall(chunk.content_or_path):
            image_paths.append(match)
        for image_path in image_paths:
            if file_opr.get_type(image_path) != 'image':
                continue

            if image_path.startswith('http'):
                continue

            if not os.path.isabs(image_path):
                image_path = os.path.join(dirname, image_path)

            if os.path.exists(image_path):
                c = Chunk(content_or_path=image_path,
                          metadata=metadata.copy(),
                          modal='image')
                image_chunks.append(c)
            else:
                logger.error(
                    f'image cannot access. file: {filepath}, image path: {image_path}'
                )

    # logger.info('{} text_chunks, {} image_chunks'.format(len(text_chunks), len(image_chunks)))
    return text_chunks + image_chunks

def clean_md(text: str):
    """Remove parts of the markdown document that do not contain the key
    question words, such as code blocks, URL links, etc."""
    # remove ref
    pattern_ref = r'\[(.*?)\]\(.*?\)'
    new_text = re.sub(pattern_ref, r'\1', text)

    # remove code block
    pattern_code = r'```.*?```'
    new_text = re.sub(pattern_code, '', new_text, flags=re.DOTALL)

    # remove underline
    new_text = re.sub('_{5,}', '', new_text)

    # remove table
    # new_text = re.sub('\|.*?\|\n\| *\:.*\: *\|.*\n(\|.*\|.*\n)*', '', new_text, flags=re.DOTALL)   # noqa E501

    # use lower
    new_text = new_text.lower()
    return new_text

