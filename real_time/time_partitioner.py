from model.game_state import GameState, PendingMove, AirbornePiece


class TimePartitioner:
    def partition(self, state: GameState) -> tuple[list[PendingMove], list[AirbornePiece]]:
        ready = [m for m in state.pending_moves if m.arrival <= state.current_time]
        state.pending_moves = [m for m in state.pending_moves if m.arrival > state.current_time]
        landed = [a for a in state.airborne if a.landing_time <= state.current_time]
        state.airborne = [a for a in state.airborne if a.landing_time > state.current_time]
        return ready, landed
