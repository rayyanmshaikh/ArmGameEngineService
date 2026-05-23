import os
import subprocess
import sys
from typing import Optional


class StockfishAdapter:
    def __init__(self, path: Optional[str] = None):
        # default bundled path inside repo
        default_windows = os.path.join(os.getcwd(), 'third_party', 'stockfish', 'stockfish.exe')
        default_unix = os.path.join(os.getcwd(), 'third_party', 'stockfish', 'stockfish')
        bundled_dir = os.path.join(os.getcwd(), 'third_party', 'stockfish')
        env_path = os.environ.get('STOCKFISH_PATH')

        def discover_bundled_binary() -> Optional[str]:
            if not os.path.isdir(bundled_dir):
                return None
            if sys.platform.startswith('win'):
                candidates = [
                    os.path.join(bundled_dir, name)
                    for name in os.listdir(bundled_dir)
                    if name.lower().endswith('.exe')
                ]
            else:
                candidates = [
                    os.path.join(bundled_dir, name)
                    for name in os.listdir(bundled_dir)
                    if os.path.isfile(os.path.join(bundled_dir, name))
                    and not name.lower().endswith('.txt')
                ]
            return candidates[0] if candidates else None

        if path:
            self.path = path
        elif env_path:
            self.path = env_path
        else:
            preferred = default_windows if sys.platform.startswith('win') else default_unix
            self.path = preferred if os.path.isfile(preferred) else (discover_bundled_binary() or preferred)

    def choose_move(self, fen: str, movetime_ms: int = 100) -> Optional[str]:
        if not os.path.isfile(self.path):
            raise FileNotFoundError(f'Stockfish binary not found at {self.path}')
        # start stockfish process
        proc = subprocess.Popen(
            [self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        try:
            # send position and go command
            cmds = f'position fen {fen}\n'
            cmds += f'go movetime {movetime_ms}\n'
            stdout, stderr = proc.communicate(cmds, timeout=(movetime_ms / 1000.0) + 1)
        except subprocess.TimeoutExpired:
            proc.kill()
            return None
        finally:
            if proc.poll() is None:
                proc.kill()

        # parse bestmove from stdout
        for line in stdout.splitlines():
            if line.startswith('bestmove'):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
        return None
