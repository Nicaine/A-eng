import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# ---------- Filesystem root ----------

# Use a local "data" directory inside the app folder
ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# ---------- MCP setup ----------

mcp = FastMCP("auth-eng-filesystem")


@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.

    subpath is relative to the ROOT directory.
    """
    base = (ROOT / subpath).resolve()

    # Safety: don't allow escaping the root dir
    if ROOT not in base.parents and base != ROOT:
        raise ValueError("Path is outside the allowed root directory")

    if not base.exists():
        return []

    return [str(p.relative_to(ROOT)) for p in sorted(base.iterdir())]


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read a UTF-8 text file relative to the MCP root directory.
    """
    full = (ROOT / path).resolve()

    if ROOT not in full.parents:
        raise ValueError("Path is outside the allowed root directory")

    if not full.is_file():
        raise FileNotFoundError(f"No such file: {path}")

    return full.read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """
    Write a UTF-8 text file under the MCP root directory.
    Overwrites the file if it already exists.
    """
    full = (ROOT / path).resolve()

    if ROOT not in full.parents:
        raise ValueError("Path is outside the allowed root directory")

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return f"Saved {full.relative_to(ROOT)}"


# ---------- FastAPI app ----------

app = FastAPI()


@app.get("/")
async def health():
    """
    Simple health check so you can hit https://a-eng.onrender.com
    in the browser and confirm the server is alive.
    """
    return {
        "status": "ok",
        "message": "MCP filesystem server is running",
        "root_dir": str(ROOT),
    }


@app.get("/sse")
async def sse(request: Request):
    """
    SSE endpoint used by ChatGPT MCP connectors.

    ChatGPT will call this with the correct headers; in the browser you
    may see an error JSON if you hit it directly, which is fine.
    """
    return await mcp.sse_handler(request)
