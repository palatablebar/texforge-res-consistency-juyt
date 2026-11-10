"""共享卷静态文件访问：/files/previews/... 与 /files/artifacts/..."""
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config.settings import settings

router = APIRouter(prefix="/files", tags=["files"])


def _safe_join(root: str, rel_path: str) -> str:
    target = os.path.realpath(os.path.join(root, rel_path))
    root_real = os.path.realpath(root)
    if not target.startswith(root_real + os.sep):
        raise HTTPException(status_code=400, detail="非法路径")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="文件不存在")
    return target


@router.get("/previews/{rel_path:path}")
def preview_file(rel_path: str):
    return FileResponse(_safe_join(settings.PREVIEW_DIR, rel_path))


@router.get("/artifacts/{rel_path:path}")
def artifact_file(rel_path: str):
    return FileResponse(_safe_join(settings.ARTIFACT_DIR, rel_path))
