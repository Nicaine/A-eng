import os
from pathlib import Path

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# -------------------------------------------------
# Filesystem root (inside the Render app directory)
# -------------------------------------------------
#
# This is *ephemeral* storage (wiped on each deploy),
# but totally fine for an MCP filesystem sandbox.
#

ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# MCP server definition
# -------------------------------------------------

mcp = FastMCP("auth-eng-fs")


@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.

    Arguments:
    - subpath: path relative to the root directory.
    """
    base = (ROOT / subpath).resolve()

    # Safety: don't allow escaping the root directory
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
    Read a UTF-8 text file from the MCP root directory.

    Arguments:
    - path: file path relative to the root directory.
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

    Arguments:
    - path: file path relative to the root directory.
    - content: text content to write.
    """
    full = (ROOT / path).resolve()

    if ROOT not in full.parents:
        raise ValueError("Path is outside the allowed root directory")

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")

    return f"Saved {full.relative_to(ROOT)}"


# -------------------------------------------------
# FastAPI app + MCP SSE endpoint
# -------------------------------------------------

app = FastAPI(title="Auth-Eng Filesystem MCP")


@app.get("/")
async def status():
    """
    Simple health-check so you can hit https://a-eng.onrender.com/
    in a browser and see that the server is alive.
    """
    return {
        "status": "ok",
        "message": "MCP filesystem server is running",
        "root_dir": str(ROOT),
    }


# FastMCP exposes a FastAPI-compatible ASGI app that speaks
# MCP over HTTP+SSE. We mount it at /sse, which is what the
# ChatGPT connector will call.
mcp_app = mcp.fastapi_app()  # <-- if logs say this attribute doesn't exist, tell me

app.mount("/sse", mcp_app)
