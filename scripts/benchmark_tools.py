"""CLI entry point for the canonical native text/vision benchmark."""

import asyncio
import sys
from pathlib import Path

from murdoku_lab.evaluation.tools import main, p

if __name__ == "__main__":
    asyncio.run(main(p.parse_args()))
