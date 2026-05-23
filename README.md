# Arm Game Engine Service

Python chess game engine running python-chess and Stockfish in a Docker container to take POST requests of human moves and GET requests of AI moves.
Will be able to run games locally through terminal (for validation) with API endpoints to work in conjunction with other microservices for the chess robot arm.

Defaults:

-- Stockfish binary: auto-detected from `third_party/stockfish/` (Windows: first `.exe` found). You can set `STOCKFISH_PATH` to override.

- Configure Stockfish options with `config/stockfish.yaml` (see `config/stockfish.yaml`). Options include `skill_level`, `limit_strength`, `elo`, `threads`, and `hash_mb`.
- Robot service URL: set `ROBOT_SERVICE_URL` environment variable to enable sending moves to a robot.

Run API (after installing `requirements.txt`):

```bash
python -m src.main
```

Run CLI:

```bash
python -m src.main --cli
```
