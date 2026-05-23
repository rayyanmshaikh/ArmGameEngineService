import os
import subprocess
import sys
from typing import Optional
import yaml


class StockfishAdapter:
    def __init__(self, path: Optional[str] = None):
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

        self.default_options = {
            'Skill Level': None,
            'UCI_LimitStrength': None,
            'UCI_Elo': None,
            'Threads': None,
            'Hash': None,
        }

        # Load config
        cfg_path = os.path.join(os.getcwd(), 'config', 'stockfish.yaml')
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f) or {}

                if not path and not env_path and cfg.get('path'):
                    self.path = cfg.get('path')

                map_cfg = {
                    'Skill Level': cfg.get('skill_level'),
                    'UCI_LimitStrength': cfg.get('limit_strength'),
                    'UCI_Elo': cfg.get('elo'),
                    'Threads': cfg.get('threads'),
                    'Hash': cfg.get('hash_mb'),
                }

                for k, v in map_cfg.items():
                    if v is not None:
                        self.default_options[k] = v

                self.default_movetime_ms = cfg.get('default_movetime_ms')
            except Exception:
                self.default_movetime_ms = None
        else:
            self.default_movetime_ms = None

    def choose_move(self, fen: str, movetime_ms: int = 100, options: Optional[dict] = None) -> Optional[str]:
        if not os.path.isfile(self.path):
            raise FileNotFoundError(f'Stockfish binary not found at {self.path}')
        # start stockfish process
        proc = subprocess.Popen(
            [self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        try:
            # prepare UCI initialization and options
            cmds = 'uci\n'
            # merge defaults with passed options
            merged = dict(self.default_options)
            if options:
                merged.update(options)
            # send setoption for any provided option values
            for name, val in merged.items():
                if val is None:
                    continue
                # ensure boolean values are formatted as 'true'/'false'
                if isinstance(val, bool) or str(val).lower() in ('true', 'false'):
                    v = str(val).lower()
                else:
                    v = str(val)
                cmds += f'setoption name {name} value {v}\n'

            cmds += 'isready\n'
            cmds += f'position fen {fen}\n'
            # prefer movetime passed, otherwise config default, otherwise parameter
            final_movetime = movetime_ms or self.default_movetime_ms or 100
            cmds += f'go movetime {final_movetime}\n'

            stdout, stderr = proc.communicate(cmds, timeout=(movetime_ms / 1000.0) + 2)
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
