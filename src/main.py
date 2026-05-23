import os
import argparse
from fastapi import FastAPI
import uvicorn

from .api.routes import router
from .game.stockfish_engine import StockfishAdapter

app = FastAPI(title='Arm Game Engine')
app.include_router(router)


def run_api(host: str = '0.0.0.0', port: int = 8000):
    uvicorn.run('src.main:app', host=host, port=port, reload=False)


def run_cli():
    from .game.state import GAME
    sf = StockfishAdapter()
    print('Starting CLI mode — type moves in UCI format (e2e4). Type quit to exit.')
    GAME.start()
    while True:
        print('\nFEN:', GAME.fen())
        mv = input('Your move: ').strip()
        if mv in ('quit', 'exit'):
            break
        ok, reason = GAME.apply_human_move(mv)
        if not ok:
            print('Move rejected:', reason)
            continue
        print('Human move accepted.')
        try:
            ai_move = sf.choose_move(GAME.fen())
        except FileNotFoundError as e:
            print('Stockfish not found:', e)
            return
        if not ai_move:
            print('No ai move returned')
            return
        GAME.apply_ai_move(ai_move)
        print('AI move:', ai_move)
        input('Press Enter after robot move completed (simulated)...')
        GAME.waiting_for_robot = False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if args.cli:
        run_cli()
    else:
        run_api(port=args.port)
