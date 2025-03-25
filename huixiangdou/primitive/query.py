
from dataclasses import dataclass, field
from enum import Enum
import math

# Copy from langchain
class DistanceStrategy(str, Enum):
    """Enumerator of the Distance strategies for calculating distances
    between vectors."""
    EUCLIDEAN_DISTANCE = "EUCLIDEAN_DISTANCE"
    MAX_INNER_PRODUCT = "MAX_INNER_PRODUCT"
    UNKNOWN = 'UNKNOWN'

    @staticmethod
    def euclidean_relevance_score_fn(distance: float) -> float:
        """Return a similarity score on a scale [0, 1]."""
        # The 'correct' relevance function
        # may differ depending on a few things, including:
        # - the distance / similarity metric used by the VectorStore
        # - the scale of your embeddings (OpenAI's are unit normed. Many
        #  others are not!)
        # - embedding dimensionality
        # - etc.
        # This function converts the Euclidean norm of normalized embeddings
        # (0 is most similar, sqrt(2) most dissimilar)
        # to a similarity function (0 to 1)
        return 1.0 - distance / math.sqrt(2)

    @staticmethod
    def max_inner_product_relevance_score_fn(similarity: float) -> float:
        """Normalize the distance to a score on a scale [0, 1]."""
        return similarity

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
            formatted += f"text='{self.text}' "
        if self.image is not None:
            formatted += f"image='{self.image}' "
        if self.audio is not None:
            formatted += f"audio='{self.audio}' "
        return formatted

    def __repr__(self) -> str:
        return self.__str__()
