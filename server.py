import os
from pathlib import Path

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# ----- Config -----
# Use a local "data" folder inside the app directory (writable on Render free)
ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("auth-eng-fs")

# ----- Tools -----

@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.
    Paths are always relative to the ROOT.
    """
    base = (ROOT / subpath).resolve()

    # Safety: don't allow escaping the root dir
    if ROOT not in base.parents and base != ROOT:
        raise ValueError("Path is outside the allowed root directory")

    if not base.exists():
        return []

    return [
        str(p.relative_to(ROOT))
        for p in sorted(base.iterdir())
    ]


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read a text file from the MCP root.
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
    Write a text file under the MCP root. Overwrites if it exists.
    """
    full = (ROOT / path).resolve()
    if ROOT not in full.parents:
        raise ValueError("Path is outside the allowed root directory")

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return f"Saved {full.relative_to(ROOT)}"


# ----- HTTP / MCP wiring -----

# Build the MCP ASGI app
mcp_app = mcp.http_app()

# Wrap it in FastAPI so uvicorn can serve it
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

# MCP endpoint for ChatGPT
app.mount("/mcp", mcp_app)
