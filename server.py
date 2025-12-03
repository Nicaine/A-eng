from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# ---------- CONFIG: root folder for your "filesystem" ----------

# This will be something like /opt/render/project/src/data on Render
ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# ---------- MCP SERVER ----------

mcp = FastMCP("auth-eng-fs")

# ---------- TOOLS ----------


@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.

    Args:
        subpath: path *relative* to ROOT (default ".")
    """
    base = (ROOT / subpath).resolve()

    # Safety: don't allow escaping ROOT
    if ROOT not in base.parents and base != ROOT:
        raise ValueError("Path is outside the allowed root directory")

    if not base.exists():
        return []

    return [str(p.relative_to(ROOT)) for p in sorted(base.iterdir())]


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read a text file under the MCP root.
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


# ---------- HTTP VIEWS (for browsers / health checks) ----------


async def root_status(request):
    """
    Simple JSON status at "/".
    Nice for sanity-checking in a browser.
    """
    return JSONResponse(
        {
            "status": "ok",
            "message": "MCP filesystem server is running",
            "root_dir": str(ROOT),
        }
    )


async def mcp_status(request):
    """
    JSON status at "/mcp" so the MCP client doesn't see 404.
    """
    return JSONResponse(
        {
            "status": "ok",
            "kind": "mcp-http-endpoint",
            "endpoints": {
                "sse": "/mcp/sse",
                "messages": "/mcp/messages",
            },
        }
    )


# FastMCP provides an ASGI app with /sse and /messages
sse_starlette_app = mcp.sse_app()

# ---------- MAIN ASGI APP (what uvicorn runs) ----------

app = Starlette(
    routes=[
        # Human / health endpoints
        Route("/", root_status),
        Route("/status", root_status),
        Route("/mcp", mcp_status),
        # MCP SSE & message endpoints live under /mcp
        Mount("/mcp", app=sse_starlette_app),
    ]
)
