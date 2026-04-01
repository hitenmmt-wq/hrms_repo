"""Django management command to run HRMS FastMCP server."""

from django.core.management.base import BaseCommand

from apps.ai.fastmcp_server import create_mcp_server


class Command(BaseCommand):
    help = "Start the HRMS FastMCP server for Claude and MCP clients"

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            type=str,
            default="localhost",
            help="Host to listen on (default: localhost)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8001,
            help="Port to listen on (default: 8001)",
        )

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Starting HRMS FastMCP Server on {host}:{port}...")
        )
        self.stdout.write(
            self.style.WARNING("Claude and MCP clients can now connect to your tools")
        )

        mcp = create_mcp_server()
        mcp.run()
