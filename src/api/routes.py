from fastapi import APIRouter, BackgroundTasks, HTTPException
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


def send_robot_move_task(ai_move: str):
    payload = {'from': ai_move[:2], 'to': ai_move[2:], 'move': ai_move}
    try:
        send_move_to_robot(payload)
    except Exception:
        GAME.set_pending_feedback({'type': 'robot_error', 'message': 'failed to send to robot'})


@router.get('/health')
def health():
    state_snapshot = GAME.snapshot()
    return {'status': 'ok', **state_snapshot}


@router.post('/start')
def start():
    GAME.start()
    return {'status': 'started', 'fen': GAME.fen()}


@router.post('/human-move')
def human_move(req: HumanMoveRequest, background_tasks: BackgroundTasks):
    ok, reason = GAME.apply_human_move(req.move)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    # ask stockfish for an answer
    try:
        ai_move = sf.choose_move(GAME.fen())
    except FileNotFoundError as e:
        # Stockfish not available
        pending = {'type': 'ai_error', 'message': str(e)}
        GAME.set_pending_feedback(pending)
        return {'status': 'ok', 'pending': pending}

    if not ai_move:
        pending = {'type': 'ai_error', 'message': 'no move from stockfish'}
        GAME.set_pending_feedback(pending)
        return {'status': 'ok', 'pending': pending}

    # apply AI move to internal board and set waiting_for_robot
    applied = GAME.apply_ai_move(ai_move)
    if not applied:
        raise HTTPException(status_code=500, detail='ai move illegal')

    # send to robot without blocking API response
    background_tasks.add_task(send_robot_move_task, ai_move)

    return {'status': 'ok', 'ai_move': ai_move, 'fen': GAME.fen()}


@router.post('/robot-done')
def robot_done(req: RobotDoneRequest):
    # called by robot when it finishes moving
    GAME.mark_robot_done()
    return {'status': 'ok'}


@router.get('/state')
def state():
    return GAME.snapshot()


@router.post('/stop')
def stop():
    GAME.start()
    return {'status': 'stopped'}
