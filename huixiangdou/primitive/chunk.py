from dataclasses import asdict, dataclass, field
from enum import Enum

class Modal(Enum):
    TEXT = 'text'
    IMAGE = 'image'
    AUDIO = 'audio'

# modified from langchain
class Chunk():
    """Class for storing a piece of text and associated metadata.

    Example:

        .. code-block:: python

            from huixiangdou.primitive import Chunk

            chunk = Chunk(
                content_or_path="Hello, world!",
                metadata={"source": "https://example.com"}
            )
    """
    modal: Modal = Modal.TEXT
    content_or_path: str = ''
    metadata: dict = {}

    def __init__(self, modal:Modal=Modal.TEXT, content_or_path:str='', metadata:dict={}):
        self.modal = modal
        self.content_or_path = content_or_path
        self.metadata = metadata

    def __str__(self) -> str:
        """Override __str__ to restrict it to content_or_path and metadata."""
        # The format matches pydantic format for __str__.
        #
        # The purpose of this change is to make sure that user code that
        # feeds Document objects directly into prompts remains unchanged
        # due to the addition of the id field (or any other fields in the future).
        #
        # This override will likely be removed in the future in favor of
        # a more general solution of formatting content directly inside the prompts.
        if self.metadata:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}' metadata={self.metadata}"
        else:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}'"

    def __repr__(self) -> str:
        return self.__str__()
