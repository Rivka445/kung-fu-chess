from abc import ABC, abstractmethod


# ---- Base Status (Strategy Pattern) ----

class PieceStatus(ABC):
    """
    Abstract base for all piece statuses.
    Each status defines whether the piece can act and provides a name for logging.
    Follows the Strategy Pattern — callers use can_act() without knowing the concrete status.
    """

    @abstractmethod
    def can_act(self) -> bool:
        """Return True if the piece is allowed to perform a move."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Return a string identifier for this status (used in logging/debugging)."""
        ...


# ---- Concrete Statuses ----

class IdleStatus(PieceStatus):
    """The piece is idle and ready to move."""
    def can_act(self) -> bool: return True
    def name(self) -> str: return "idle"


class InFlightStatus(PieceStatus):
    """The piece is currently in motion — either travelling to a target or landing."""
    def can_act(self) -> bool: return False
    def name(self) -> str: return "in_flight"


class OnCooldownStatus(PieceStatus):
    """The piece recently moved and must wait until a given time before acting again."""
    def __init__(self, until: int):
        # The timestamp at which the cooldown expires
        self._until = until

    def can_act(self) -> bool: return False
    def name(self) -> str: return f"cooldown_until_{self._until}"
