"""Download one immutable query/rollout dataset snapshot into a dedicated directory."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_snapshot(snapshot, output, repo, revision, overwrite=False):
    if overwrite:
        raise ValueError("Overwrite is unsupported; choose a fresh output directory")
    snapshot, output = Path(snapshot), Path(output)
    files = {
        p.relative_to(snapshot).as_posix(): p
        for p in snapshot.rglob("*")
        if p.is_file()
        and (
            p.relative_to(snapshot).as_posix() in ("query_rollouts.jsonl", "README.md")
            or (p.parent == snapshot and p.name.startswith(("LICENSE", "NOTICE")))
            or p.relative_to(snapshot).parts[0] == "images"
        )
    }
    if "query_rollouts.jsonl" not in files:
        raise FileNotFoundError("Dataset does not contain query_rollouts.jsonl")
    hashes = {name: file_hash(path) for name, path in files.items()}
    receipt = {"repo": repo, "revision": revision, "files": hashes}
    if output.exists():
        previous = output / "receipt.json"
        if previous.exists() and json.loads(previous.read_text()) != receipt:
            raise ValueError(
                "Output belongs to a different snapshot; choose a new directory"
            )
        existing = {
            p.relative_to(output).as_posix(): p
            for p in output.rglob("*")
            if p.is_file()
        }
        unexpected = set(existing) - set(files) - {"receipt.json"}
        if unexpected:
            raise ValueError(
                "Output must be a dedicated dataset directory without extra files"
            )
        for name, path in existing.items():
            if (
                name != "receipt.json"
                and name in hashes
                and file_hash(path) != hashes[name]
            ):
                raise ValueError(
                    "Existing content differs from target snapshot; choose a new directory"
                )
        if set(files) <= set(existing) and all(
            file_hash(existing[n]) == hashes[n] for n in files
        ):
            temporary = output / "receipt.json.tmp"
            temporary.write_text(json.dumps(receipt, indent=2) + "\n")
            temporary.replace(previous)
            return receipt
    if output.exists() and any(output.iterdir()):
        raise ValueError("Incomplete dataset snapshot; choose a fresh output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name + ".pending-", dir=output.parent))
    try:
        for name, source in files.items():
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            if file_hash(destination) != hashes[name]:
                raise ValueError("Incomplete dataset copy")
        (stage / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if output.exists():
            output.rmdir()
        stage.rename(output)
        return receipt
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="EverywhereSafety/murdoku-lab")
    parser.add_argument("--revision", default="main")
    parser.add_argument(
        "--component",
        choices=("queries", "teacher", "all"),
        default="all",
        help="Every choice downloads the unified dataset",
    )
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError:
        parser.error("Install requirements/data.txt first")
    info = HfApi().repo_info(args.repo, repo_type="dataset", revision=args.revision)
    snapshot = snapshot_download(
        args.repo,
        repo_type="dataset",
        revision=info.sha,
        allow_patterns=[
            "query_rollouts.jsonl",
            "images/**",
            "README.md",
            "LICENSE*",
            "NOTICE*",
        ],
    )
    receipt = install_snapshot(
        snapshot, args.output, args.repo, info.sha, args.overwrite
    )
    print(
        f"Downloaded {args.repo}@{receipt['revision']}: {len(receipt['files'])} files"
    )


if __name__ == "__main__":
    main()
