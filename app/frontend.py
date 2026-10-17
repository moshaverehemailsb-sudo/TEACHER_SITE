from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException


class SafeStaticFiles(StaticFiles):
    """فایل‌های ایستا را سرو می‌کند، ولی هر مسیری را که بخشی از آن با نقطه
    شروع شود (مثل .git یا .env) رد می‌کند."""

    async def get_response(self, path: str, scope):
        if any(part.startswith(".") for part in Path(path).parts):
            raise StarletteHTTPException(status_code=404)
        return await super().get_response(path, scope)


def mount_frontend(app: FastAPI, directory: str) -> None:
    if not directory:
        return
    root = Path(directory)
    if not (root / "index.html").is_file():
        raise RuntimeError(f"FRONTEND_DIR must contain index.html: {root}")
    app.mount("/", SafeStaticFiles(directory=root, html=True), name="frontend")