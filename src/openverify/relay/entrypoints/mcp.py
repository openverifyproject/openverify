"""Optional official MCP SDK adapter, exposing only host-allowlisted graphs."""

from mcp.server.fastmcp import FastMCP
from pydantic import JsonValue

from openverify.relay.entrypoints.service import GraphService


def create_server(service: GraphService | None = None) -> FastMCP[None]:
    host = service if service is not None else GraphService()
    server: FastMCP[None] = FastMCP("OpenVerify Relay")

    @server.tool()
    def list_graphs() -> list[str]:
        """List verification graphs authorized by the host."""
        return host.list_graphs()

    @server.tool()
    def describe_graph(name: str) -> dict[str, JsonValue]:
        """Describe declared typed inputs, operations, and bindings."""
        return host.describe_graph(name)

    @server.tool()
    async def run_graph(name: str, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
        """Execute a named graph and return its complete validated VCP RunRecord."""
        return await host.run_graph(name, inputs)

    @server.tool()
    def inspect_result(run_id: str) -> dict[str, JsonValue]:
        """Retrieve a retained record from this server process."""
        return host.inspect_result(run_id)

    return server


def main() -> int:
    create_server().run(transport="stdio")
    return 0
