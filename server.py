from mcp.server import Server
from mcp.types import *
from mcp import api
import os

ROOT = "/data"  # Render's persistent folder

server = Server("filesystem-mcp")

@server.tools.list
def list_tools():
    return [
        Tool(
            name="list_files",
            description="List files in the root folder",
            inputSchema={"type": "object"}
        ),
        Tool(
            name="read_file",
            description="Read a file from storage",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write text to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        )
    ]

@server.tools.call
def tools(name: str, arguments: dict):
    if name == "list_files":
        return Result(output=os.listdir(ROOT))

    if name == "read_file":
        file_path = os.path.join(ROOT, arguments["path"])
        with open(file_path, "r") as f:
            return Result(output=f.read())

    if name == "write_file":
        file_path = os.path.join(ROOT, arguments["path"])
        with open(file_path, "w") as f:
            f.write(arguments["content"])
        return Result(output="OK")

server.run()
