from abc import ABC, abstractmethod
import numpy as np


class UIComponent(ABC):
    """
    Abstract base class for all UI components (Component in the Composite Pattern).
    Defines the common interface for drawing components on a canvas.
    """

    @abstractmethod
    def draw(self, canvas: np.ndarray) -> None:
        """Draw the component on the given numpy canvas."""
        pass
