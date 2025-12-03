import os
from pathlib import Path

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# ----- Config -----
# Root directory inside the Render container where files will live
ROOT = Path(os.environ.get("FILES_ROOT", "/data")).resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# Create the MCP server
mcp = FastMCP("auth-eng-fs")

# ----- Tools -----

@mcp.tool
def list_files(subpath: str = ".") -> list[str]:
    """
    List files and folders under the MCP root directory.
    Paths are always relative to the ROOT (/data).
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


@mcp.tool
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


@mcp.tool
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

# Get an ASGI app that speaks the Streamable HTTP MCP protocol
mcp_app = mcp.http_app()

# Wrap it in a FastAPI app so we can run it with uvicorn
app = FastAPI()

# Optional tiny health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Mount MCP under /mcp
app.mount("/mcp", mcp_app)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
