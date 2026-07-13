from abc import ABC, abstractmethod


class PieceStatus(ABC):
    @abstractmethod
    def can_act(self) -> bool: ...

    @abstractmethod
    def name(self) -> str: ...


class IdleStatus(PieceStatus):
    def can_act(self) -> bool: return True
    def name(self) -> str: return "idle"


class InFlightStatus(PieceStatus):
    def can_act(self) -> bool: return False
    def name(self) -> str: return "in_flight"


class OnCooldownStatus(PieceStatus):
    def __init__(self, until: int):
        self._until = until

    def can_act(self) -> bool: return False
    def name(self) -> str: return f"cooldown_until_{self._until}"
