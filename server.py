import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------
# MCP FILESYSTEM-LIKE SERVER CONFIG
# --------------------------------------------------------------------

# Root folder where the MCP server is allowed to read/write files.
# This lives next to server.py and is writable on Render (ephemeral).
ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# Create the MCP server
mcp = FastMCP("auth-eng-fs")


# --------------------------------------------------------------------
# TOOLS
# --------------------------------------------------------------------

@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.

    Args:
        subpath: Path relative to the root "data" folder (default ".").

    Returns:
        List of relative paths (strings).
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
    Read a UTF-8 text file from the MCP root.

    Args:
        path: Path relative to the root "data" folder.

    Returns:
        File contents as a string.
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
    Write a UTF-8 text file under the MCP root. Overwrites if it exists.

    Args:
        path: Path relative to the root "data" folder.
        content: Text to write.

    Returns:
        Message describing what was saved.
    """
    full = (ROOT / path).resolve()

    if ROOT not in full.parents:
        raise ValueError("Path is outside the allowed root directory")

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")

    return f"Saved {full.relative_to(ROOT)}"


# --------------------------------------------------------------------
# ASGI APP (SSE MCP SERVER)
# --------------------------------------------------------------------

# Starlette app that exposes the MCP SSE endpoints.
# This will create:
#   /sse       -> SSE stream (text/event-stream)
#   /messages  -> HTTP endpoint for MCP messages
app = Starlette(
    routes=[
        Mount("/", app=mcp.sse_app()),
    ]
)
