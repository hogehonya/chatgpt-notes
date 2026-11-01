"""Single-tool stdio MCP entry point."""

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from notes import NoteStore


def main():
    parser = argparse.ArgumentParser(description="Save Markdown inside a fixed folder")
    parser.add_argument("--root", type=Path, default=Path.home() / "chatgpt-notes")
    args = parser.parse_args()
    store = NoteStore(args.root)
    mcp = FastMCP("chatgpt-notes")

    @mcp.tool()
    def save_note(path: str, content: str) -> dict:
        """Create or replace a Markdown note. path is relative to the fixed notes root.

        content must contain the complete desired UTF-8 text, including for updates.
        """
        return store.save_note(path, content)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
