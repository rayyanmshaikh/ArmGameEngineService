from typing import Optional
import os
import chess


class GameState:
    def __init__(self):
        self.board = chess.Board()
        self.last_human_move: Optional[str] = None
        self.last_ai_move: Optional[str] = None
        self.pending_feedback: Optional[dict] = None
        self.waiting_for_robot: bool = False

    def start(self):
        self.board.reset()
        self.last_human_move = None
        self.last_ai_move = None
        self.pending_feedback = None
        self.waiting_for_robot = False

    def fen(self) -> str:
        return self.board.fen()

    def turn(self) -> str:
        return 'white' if self.board.turn == chess.WHITE else 'black'

    def status(self) -> str:
        if self.board.is_checkmate():
            return 'checkmate'
        if self.board.is_stalemate():
            return 'stalemate'
        if self.board.is_insufficient_material():
            return 'draw_insufficient_material'
        if self.board.is_check():
            return 'check'
        return 'ongoing'

    def validate_move(self, uci_move: str) -> (bool, str):
        try:
            move = chess.Move.from_uci(uci_move)
        except Exception:
            return False, 'invalid_uci'
        if move not in self.board.legal_moves:
            return False, 'illegal_move'
        return True, 'ok'

    def apply_human_move(self, uci_move: str) -> (bool, str):
        ok, reason = self.validate_move(uci_move)
        if not ok:
            self.pending_feedback = {
                'type': 'illegal_move',
                'message': f'{uci_move} is illegal',
                'turn': 'human',
                'fen': self.fen(),
            }
            return False, reason
        move = chess.Move.from_uci(uci_move)
        self.board.push(move)
        self.last_human_move = uci_move
        self.pending_feedback = {
            'type': 'move_accepted',
            'message': f'{uci_move} accepted',
            'turn': 'ai',
            'fen': self.fen(),
        }
        return True, 'ok'

    def apply_ai_move(self, uci_move: str):
        try:
            move = chess.Move.from_uci(uci_move)
        except Exception:
            self.pending_feedback = {
                'type': 'ai_error',
                'message': f'invalid ai move {uci_move}',
            }
            return False
        if move not in self.board.legal_moves:
            self.pending_feedback = {
                'type': 'ai_illegal',
                'message': f'ai move {uci_move} illegal on current board',
            }
            return False
        self.board.push(move)
        self.last_ai_move = uci_move
        self.pending_feedback = {
            'type': 'robot_move_sent',
            'message': f'AI move {uci_move} sent to robot',
            'turn': 'human',
            'fen': self.fen(),
        }
        self.waiting_for_robot = True
        return True


# single global state used by the API
GAME = GameState()
