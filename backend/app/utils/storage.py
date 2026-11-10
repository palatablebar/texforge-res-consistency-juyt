"""共享卷文件读写：ARTIFACT_DIR / PREVIEW_DIR。"""
import os
import shutil

from app.config.settings import settings


def ensure_dirs() -> None:
    os.makedirs(settings.ARTIFACT_DIR, exist_ok=True)
    os.makedirs(settings.PREVIEW_DIR, exist_ok=True)


def artifact_abs(rel_path: str) -> str:
    return os.path.join(settings.ARTIFACT_DIR, rel_path)


def preview_abs(rel_path: str) -> str:
    return os.path.join(settings.PREVIEW_DIR, rel_path)


def write_bytes(rel_path: str, data: bytes, preview: bool = False) -> str:
    root = settings.PREVIEW_DIR if preview else settings.ARTIFACT_DIR
    abs_path = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    tmp = abs_path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, abs_path)
    return rel_path


def remove_variant_dir(recipe_slug: str, revision: int) -> None:
    for root in (settings.ARTIFACT_DIR, settings.PREVIEW_DIR):
        target = os.path.join(root, recipe_slug, f"rev-{revision}")
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)


def file_size(rel_path: str, preview: bool = False) -> int:
    abs_path = preview_abs(rel_path) if preview else artifact_abs(rel_path)
    try:
        return os.path.getsize(abs_path)
    except OSError:
        return 0


def read_artifact(rel_path: str) -> bytes:
    with open(artifact_abs(rel_path), "rb") as fh:
        return fh.read()
