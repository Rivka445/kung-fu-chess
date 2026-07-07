# pieces.py

VALID_PIECE_TYPES = {'K', 'Q', 'R', 'B', 'N', 'P'}
VALID_COLORS = {'w', 'b'}

class ChessPiece:
    def __init__(self, token: str):
        """
        Represents a chess piece based on its two-character token (e.g., 'wK', 'bP').
        """
        self.token = token
        self.color = token[0] 
        self.piece_type = token[1]  

    def is_white(self) -> bool:
        return self.color == 'w'

    def is_black(self) -> bool:
        return self.color == 'b'