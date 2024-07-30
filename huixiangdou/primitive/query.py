# Copyright (c) OpenMMLab. All rights reserved.
from dataclasses import dataclass, field


@dataclass
class Query():
    text: str = None
    image: str = None
    audio: str = None

    def __str__(self) -> str:
        """Override __str__ to restrict it to text, image and audio."""
        # The format matches pydantic format for __str__.
        #
        # The purpose of this change is to make sure that user code that
        # feeds Document objects directly into prompts remains unchanged
        # due to the addition of the id field (or any other fields in the future).
        #
        # This override will likely be removed in the future in favor of
        # a more general solution of formatting content directly inside the prompts.

        formatted = ''
        if self.text is not None:
            formatted += f"text='{self.text}'"
        if self.image is not None:
            formatted += f"image='{self.image}'"
        if self.audio is not None:
            formatted += f"audio='{self.audio}'"
        return formatted

    def __repr__(self) -> str:
        return self.__str__()
