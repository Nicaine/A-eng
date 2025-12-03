import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# Writable directory inside Render
ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

# Create MCP instance
mcp = FastMCP("auth-eng-fs")

# FastAPI app
app = FastAPI()

# Allow Render proxy host headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Health endpoint (GET /)
@app.get("/")
def health():
    return {
        "status": "ok",
        "message": "MCP filesystem server is running",
        "root_dir": str(ROOT),
    }


# 🔹 SSE endpoint required by ChatGPT MCP
@app.get("/sse")
async def sse(request):
    """
    Return the MCP SSE application
    """
    return await mcp.sse_app(request)


# ---------------------------
# MCP Tools
# ---------------------------

@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    base = (ROOT / subpath).resolve()

    if ROOT not in base.parents and base != ROOT:
        raise ValueError("Path is outside the root directory")

    if not base.exists():
        return []

    return [
        str(p.relative_to(ROOT))
        for p in sorted(base.iterdir())
    ]


@mcp.tool()
def read_file(path: str) -> str:
    full = (ROOT / path).resolve()

    if ROOT not in full.parents:
        raise ValueError("Path is outside the root directory")
    if not full.exists():
        raise FileNotFoundError(f"No such file: {path}")

    return full.read_text()


@mcp.tool()
def write_file(path: str, content: str) -> str:
    full = (ROOT / path).resolve()

    if ROOT not in full.parents:
        raise ValueError("Path is outside the root directory")

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

    return f"Saved {full.relative_to(ROOT)}"
