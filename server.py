from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# ---------- CONFIG: root folder for your "filesystem" ----------
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


# ---------- HTTP APP FOR RENDER ----------

async def status(request):
    """
    Simple health/status endpoint for browsers.
    """
    return JSONResponse(
        {
            "status": "ok",
            "message": "MCP filesystem server is running",
            "root_dir": str(ROOT),
        }
    )


# FastMCP provides an SSE ASGI app (with /sse & /messages endpoints)
sse_starlette_app = mcp.sse_app()

# This is the ASGI app uvicorn will run
app = Starlette(
    routes=[
        # For human checking in browser:
        Route("/status", status),
        # MCP SSE endpoints at /sse and /messages:
        Mount("/", app=sse_starlette_app),
    ]
)
