# Arm Game Engine Service

Python chess game engine built on `python-chess` and Stockfish. It accepts human moves from ArmVisionService, chooses the AI reply, and exposes the current game state over FastAPI.

## Local run

Run the API:

```bash
python -m src.main
```

Run the terminal game loop:

```bash
python -m src.main --cli
```

## Docker

The engine image bundles Stockfish so it can run without a host installation.

Build the image:

```bash
docker build -t arm-game-engine-service .
```

Run the API container:

```bash
docker run --rm -p 8000:8000 arm-game-engine-service
```

Run the CLI mode in the same image:

```bash
docker run --rm -it arm-game-engine-service python -m src.main --cli
```

## Two-service live test

Use the compose file in this repo to start the engine and the vision service together:

```bash
docker compose -f docker-compose.test.yml up --build
```

The compose stack wires ArmVisionService to the engine with `MOVE_POST_URL=http://game-engine:8000/human-move`.

For terminal-driven testing without a robot service:

1. Start the stack.
2. Start the game from a second terminal with `POST /start`.
3. Run the vision relay CLI with `python -m src.main --relay-cli` from the ArmVisionService repo, or run it inside the container with `docker compose exec vision-service python -m src.main --relay-cli`.
4. Enter a human move like `e2e4` when prompted.
5. After the engine chooses an AI move, call `POST /robot-done` manually with `{"status":"done"}` to advance to the next turn.

## Configuration

- Stockfish path: set `STOCKFISH_PATH` to override auto-discovery. The Docker image sets it to `/usr/games/stockfish`.
- Stockfish tuning: edit `config/stockfish.yaml` for skill, ELO, threads, hash, and default movetime.
- Robot service: set `ROBOT_SERVICE_URL` when a downstream robot-arm service is available. Leaving it unset keeps the test path local.
