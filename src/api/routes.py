from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..game.state import GAME
from ..game.stockfish_engine import StockfishAdapter
from ..integrations.robot_client import send_move_to_robot

router = APIRouter()
sf = StockfishAdapter()


class HumanMoveRequest(BaseModel):
    move: str


class RobotDoneRequest(BaseModel):
    status: str


@router.get('/health')
def health():
    return {
        'status': 'ok',
        'fen': GAME.fen(),
        'turn': GAME.turn(),
        'game_status': GAME.status(),
        'waiting_for_robot': GAME.waiting_for_robot,
        'last_human_move': GAME.last_human_move,
        'last_ai_move': GAME.last_ai_move,
    }


@router.post('/start')
def start():
    GAME.start()
    return {'status': 'started', 'fen': GAME.fen()}


@router.post('/human-move')
def human_move(req: HumanMoveRequest):
    ok, reason = GAME.apply_human_move(req.move)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    # ask stockfish for an answer
    try:
        ai_move = sf.choose_move(GAME.fen())
    except FileNotFoundError as e:
        # Stockfish not available
        GAME.pending_feedback = {'type': 'ai_error', 'message': str(e)}
        return {'status': 'ok', 'pending': GAME.pending_feedback}

    if not ai_move:
        GAME.pending_feedback = {'type': 'ai_error', 'message': 'no move from stockfish'}
        return {'status': 'ok', 'pending': GAME.pending_feedback}

    # apply AI move to internal board and set waiting_for_robot
    applied = GAME.apply_ai_move(ai_move)
    if not applied:
        raise HTTPException(status_code=500, detail='ai move illegal')

    # send to robot (stub)
    try:
        send_move_to_robot({'from': ai_move[:2], 'to': ai_move[2:], 'move': ai_move})
    except Exception:
        # robot send failed; leave state waiting
        GAME.pending_feedback = {'type': 'robot_error', 'message': 'failed to send to robot'}

    return {'status': 'ok', 'ai_move': ai_move, 'fen': GAME.fen()}


@router.post('/robot-done')
def robot_done(req: RobotDoneRequest):
    # called by robot when it finishes moving
    GAME.waiting_for_robot = False
    GAME.pending_feedback = {'type': 'robot_move_complete', 'message': 'robot finished move', 'fen': GAME.fen()}
    return {'status': 'ok'}


@router.get('/state')
def state():
    return {
        'fen': GAME.fen(),
        'turn': GAME.turn(),
        'last_human_move': GAME.last_human_move,
        'last_ai_move': GAME.last_ai_move,
        'game_status': GAME.status(),
        'pending_feedback': GAME.pending_feedback,
        'waiting_for_robot': GAME.waiting_for_robot,
    }


@router.post('/stop')
def stop():
    GAME.start()
    return {'status': 'stopped'}
