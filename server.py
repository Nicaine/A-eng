import os
from pathlib import Path

from fastapi import FastAPI
from starlette.routing import Mount

from mcp.server.fastmcp import FastMCP

# -------------------------------------------------
# Config: where files are stored for this MCP server
# -------------------------------------------------
# On Render we just keep everything inside the app folder.
ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# Create the MCP server instance
mcp = FastMCP("auth-eng-fs")


# -------------------------------------------------
# MCP tools
# -------------------------------------------------
@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.
    Paths are always relative to ROOT (/data inside the app).
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


# -------------------------------------------------
# ASGI app for Render + MCP SSE endpoint
# -------------------------------------------------
# FastMCP gives us an ASGI sub-app that exposes:
#   - /sse       (Server-Sent Events stream)
#   - /messages  (HTTP POST for client -> server)
sse_app = mcp.sse_app()

# Main FastAPI app that Render runs with uvicorn
app = FastAPI()


@app.get("/")
async def root():
    # Simple health check so hitting the root URL in a browser shows *something*
    return {
        "status": "ok",
        "message": "MCP filesystem server is running",
        "root_dir": str(ROOT),
    }


# Mount the SSE MCP app at the root.
# This means:
#   - https://a-eng.onrender.com/sse       → SSE endpoint
#   - https://a-eng.onrender.com/messages  → POST endpoint
app.mount("/", sse_app)
