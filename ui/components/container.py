import numpy as np
from ui.components.base import UIComponent


class UIContainer(UIComponent):
    """
    A composite UI component that can hold and draw multiple child components
    (Composite in the Composite Pattern).
    """

    def __init__(self) -> None:
        self._components: list[UIComponent] = []

    def add(self, component: UIComponent) -> None:
        """Add a child component to the container."""
        self._components.append(component)

    def remove(self, component: UIComponent) -> None:
        """Remove a child component from the container."""
        self._components.remove(component)

    def draw(self, canvas: np.ndarray) -> None:
        """Draw all child components on the canvas."""
        for component in self._components:
            component.draw(canvas)
