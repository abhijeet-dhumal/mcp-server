#!/usr/bin/env python3
"""Update PROGRESS.md with current stage status and benchmarks."""

import json
import re
from datetime import datetime
from pathlib import Path


def update_progress(stage: int, benchmark_file: str | None = None) -> None:
    progress_path = Path("PROGRESS.md")
    content = progress_path.read_text()

    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    content = re.sub(r"Last update: .*", f"Last update: {now}", content)

    if benchmark_file and Path(benchmark_file).exists():
        with open(benchmark_file) as f:
            data = json.load(f)
        
        latency = data.get("tool_latency_p95_ms", "N/A")
        memory = data.get("memory_mb", "N/A")
        tokens = data.get("token_usage", "N/A")
        
        benchmark_row = f"| {stage} | {datetime.now().strftime('%Y-%m-%d')} | {latency}ms | {memory} | {tokens} |"
        
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("## Recent Changes"):
                lines.insert(i, benchmark_row)
                break
        
        content = "\n".join(lines)

    progress_path.write_text(content)
    print(f"Updated PROGRESS.md for stage {stage}")


if __name__ == "__main__":
    import sys
    stage = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    benchmark = sys.argv[2] if len(sys.argv) > 2 else None
    update_progress(stage, benchmark)
