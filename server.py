from pathlib import Path
from mcp.server.fastmcp import FastMCP

ROOT = (Path(__file__).parent / "data").resolve()
ROOT.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("auth-eng-fs")

# --------- TOOLS ---------
@mcp.tool()
def list_files(subpath: str = ".") -> list[str]:
    base = (ROOT / subpath).resolve()
    if ROOT not in base.parents and base != ROOT:
        raise ValueError("Outside root")
    if not base.exists():
        return []
    return [str(p.relative_to(ROOT)) for p in sorted(base.iterdir())]

@mcp.tool()
def read_file(path: str) -> str:
    full = (ROOT / path).resolve()
    if ROOT not in full.parents:
        raise ValueError("Outside root")
    if not full.is_file():
        raise FileNotFoundError(path)
    return full.read_text()

@mcp.tool()
def write_file(path: str, content: str):
    full = (ROOT / path).resolve()
    if ROOT not in full.parents:
        raise ValueError("Outside root")
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return f"Saved {full.relative_to(ROOT)}"

# --------- RUN SSE SERVER ---------
if __name__ == "__main__":
    mcp.run()
