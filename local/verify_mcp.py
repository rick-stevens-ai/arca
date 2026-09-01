#!/usr/bin/env python3
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    params = StdioServerParameters(
        command="/Users/stevens/code/corpus-rag/.venv/bin/python",
        args=["/Users/stevens/code/corpus-rag/server.py"])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            res = await s.call_tool("corpus_list", {})
            print("corpus_list via MCP:\n" + res.content[0].text)

asyncio.run(main())
