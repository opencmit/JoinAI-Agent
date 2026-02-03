import os
import signal
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv


def _iter_server_files() -> list[Path]:
    here = Path(__file__).resolve().parent
    files = []
    for p in sorted(here.glob("*_http_server.py")):
        if p.name.startswith("_"):
            continue
        files.append(p)
    return files


def main() -> None:
    load_dotenv()
    server_files = _iter_server_files()
    if not server_files:
        raise RuntimeError("未找到可启动的 MCP 服务文件（*_http_server.py）")

    procs: list[subprocess.Popen] = []
    required_env_by_file = {
        "serper_http_server.py": ["SERPER_API_KEY"],
        "serpapi_http_server.py": ["SERPAPI_API_KEY"],
        "jina_http_server.py": ["JINA_API_KEY"],
        # baidu 和 duckduckgo 不需要 API Key，所以不在这里列出
    }

    def _terminate_all() -> None:
        for proc in procs:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except Exception:
                try:
                    if proc.poll() is None:
                        proc.kill()
                except Exception:
                    pass

    def _handle_signal(signum: int, _frame) -> None:
        _terminate_all()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    env = os.environ.copy()

    for file_path in server_files:
        required = required_env_by_file.get(file_path.name, [])
        if required and any(not env.get(k) for k in required):
            continue
        proc = subprocess.Popen(
            [sys.executable, str(file_path)],
            cwd=str(file_path.parent.parent),
            env=env,
        )
        procs.append(proc)

    try:
        while True:
            for proc in list(procs):
                code = proc.poll()
                if code is not None and code != 0:
                    _terminate_all()
                    raise SystemExit(code)
            signal.pause()
    finally:
        _terminate_all()


if __name__ == "__main__":
    main()
