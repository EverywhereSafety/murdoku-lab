"""Build the whole site and serve it locally: the player, the daily cases and the Lab.

    python scripts/release_local.py              # http://127.0.0.1:4173/
    python scripts/release_local.py --lan        # also reachable from phones on this network
    python scripts/release_local.py --no-build   # serve the last build

Steps: case bundles (classics, the training case and the frozen showcase), daily cases with
link-preview pages pointing at this server, brand assets, a design-token drift check, the Vite
build, then the Lab server, which serves the static player at / and the research Lab (with its
Python API) at /lab/. Nothing is published anywhere; stop it with Ctrl-C.

Preview switches for the player: ?date=YYYY-MM-DD plays as if it were that day,
?unlock=all opens the whole season, ?case=<id> or ?d=<n> opens one case.
"""

import argparse
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def lan_address():
    """This machine's address on the local network, without sending anything."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def run(*command):
    print("→", " ".join(str(c) for c in command), flush=True)
    subprocess.run(command, check=True, cwd=ROOT)


def prepare_assets(site_url):
    """Rebuild public assets from versioned content, without generating new puzzles."""
    run(PYTHON, "-m", "murdoku_lab.visual.play_export")
    run(PYTHON, "-m", "murdoku_lab.setter.daily", "build", "--site-url", site_url)
    run(PYTHON, "scripts/build_brand_assets.py")
    run(PYTHON, "-m", "murdoku_lab.visual.art.design_tokens", "--check")


def build(site_url):
    prepare_assets(site_url)
    run("npm", "run", "build")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--lan", action="store_true", help="listen on all interfaces")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    lan = lan_address() if args.lan else None
    host = lan or "127.0.0.1"
    site_url = f"http://{host}:{args.port}/"
    if not args.no_build:
        build(site_url)
    print("\nMurdoku Lab, local release")
    print(f"  player   http://127.0.0.1:{args.port}/")
    if lan:
        print(f"  phone    http://{lan}:{args.port}/   (same Wi-Fi)")
    print(
        f"  today    http://127.0.0.1:{args.port}/?d=<n>   or ?date=YYYY-MM-DD, ?unlock=all"
    )
    print(f"  lab      http://127.0.0.1:{args.port}/lab/\n", flush=True)
    showcase = ROOT / "outputs" / "showcase" / "cases.jsonl"
    command = [
        PYTHON,
        "-m",
        "murdoku_lab.visual.server",
        "--host",
        "0.0.0.0" if args.lan else "127.0.0.1",
        "--port",
        str(args.port),
    ]
    if showcase.exists():
        command += ["--records", str(showcase)]
    try:
        subprocess.run(command, cwd=ROOT)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
