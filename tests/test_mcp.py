import asyncio
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTests(unittest.TestCase):
    def test_protocol_and_save(self):
        asyncio.run(asyncio.wait_for(self.check_protocol(), timeout=60))

    async def check_protocol(self):
        with tempfile.TemporaryDirectory() as root:
            params = StdioServerParameters(
                command=sys.executable,
                args=[
                    str(Path(__file__).resolve().parents[1] / "server.py"),
                    "--root",
                    root,
                ],
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listing = await session.list_tools()
                    self.assertEqual([t.name for t in listing.tools], ["save_note"])
                    result = await session.call_tool(
                        "save_note", {"path": "notes/test.md", "content": "# メモ\n"}
                    )
                    self.assertFalse(result.isError)
                    self.assertEqual(
                        (Path(root) / "notes/test.md").read_text(), "# メモ\n"
                    )
                    result = await session.call_tool(
                        "save_note", {"path": "../escape.md", "content": "bad"}
                    )
                    self.assertTrue(result.isError)
                    result = await session.call_tool(
                        "save_note", {"path": "notes/test.md", "content": "更新"}
                    )
                    self.assertFalse(result.isError)
                    self.assertEqual((Path(root) / "notes/test.md").read_text(), "更新")
