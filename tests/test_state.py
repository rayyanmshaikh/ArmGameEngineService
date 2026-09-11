import threading

import chess

from src.game.state import GameState


def test_start_resets_board_and_flags():
    state = GameState()
    state.apply_human_move("e2e4")
    state.apply_ai_move("e7e5")

    state.start()

    assert state.fen() == chess.Board().fen()
    assert state.last_human_move is None
    assert state.last_ai_move is None
    assert state.pending_feedback is None
    assert state.waiting_for_robot is False


def test_apply_human_move_rejects_invalid_and_illegal():
    state = GameState()

    ok, reason = state.apply_human_move("bad")
    assert ok is False
    assert reason == "invalid_uci"

    ok, reason = state.apply_human_move("e7e5")
    assert ok is False
    assert reason == "illegal_move"


def test_apply_human_move_accepts_legal_move():
    state = GameState()

    ok, reason = state.apply_human_move("e2e4")

    assert ok is True
    assert reason == "ok"
    assert state.last_human_move == "e2e4"
    assert state.turn() == "black"


def test_apply_ai_move_rejects_invalid_and_illegal():
    state = GameState()

    assert state.apply_ai_move("bad") is False
    assert state.pending_feedback["type"] == "ai_error"

    assert state.apply_ai_move("e7e5") is False
    assert state.pending_feedback["type"] == "ai_illegal"


def test_apply_ai_move_accepts_legal_and_sets_waiting_flag():
    state = GameState()
    ok, _ = state.apply_human_move("e2e4")
    assert ok is True

    applied = state.apply_ai_move("e7e5")

    assert applied is True
    assert state.last_ai_move == "e7e5"
    assert state.waiting_for_robot is True
    assert state.pending_feedback["type"] == "robot_move_sent"


def test_concurrent_access_does_not_corrupt_state():
    state = GameState()
    errors = []

    def worker_one():
        try:
            for _ in range(100):
                state.start()
                state.apply_human_move("e2e4")
                state.fen()
                state.status()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def worker_two():
        try:
            for _ in range(100):
                state.start()
                state.apply_human_move("d2d4")
                state.apply_ai_move("d7d5")
                state.fen()
                state.turn()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    t1 = threading.Thread(target=worker_one)
    t2 = threading.Thread(target=worker_two)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors

    # FEN should remain parseable if state stayed consistent.
    chess.Board(state.fen())
