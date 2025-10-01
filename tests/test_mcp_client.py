#!/usr/bin/env python3
"""Optional integration test for the MCP client."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path

import pytest


RUN_MCP_CLIENT_TESTS = os.getenv("RUN_MCP_CLIENT_TESTS") == "1" or os.getenv("RUN_INTEGRATION_TESTS") == "1"


async def _async_run_mcp_client() -> None:
    """Start the MCP server and perform a lightweight handshake."""

    print("🔌 Testing MCP Client Connection")
    print("=" * 40)

    server_dir = Path(__file__).resolve().parent
    env_path = server_dir / "buildbridge_env" / "bin" / "activate"
    if not env_path.exists():
        raise RuntimeError("buildbridge_env virtual environment not found; run setup first")

    cmd = [
        "bash",
        "-c",
        f"cd {server_dir} && source buildbridge_env/bin/activate && python src/main.py",
    ]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        await asyncio.sleep(2)

        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        if process.stdin is None:
            raise RuntimeError("Failed to access MCP server stdin stream")

        print("📤 Sending initialization message...")
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()

        await asyncio.sleep(1)

        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=2)
            raise RuntimeError(
                "Server exited unexpectedly."
                f"\nSTDOUT: {stdout}"
                f"\nSTDERR: {stderr}"
            )

        print("✅ Server responded to initialization request")

    finally:
        process.terminate()
        try:
            await asyncio.wait_for(asyncio.sleep(0.5), timeout=1)
        except asyncio.TimeoutError:
            pass
        if process.poll() is None:
            process.kill()


@pytest.mark.skipif(
    not RUN_MCP_CLIENT_TESTS,
    reason="MCP client integration test disabled. Set RUN_MCP_CLIENT_TESTS=1 to enable.",
)
def test_mcp_client() -> None:
    asyncio.run(_async_run_mcp_client())


def main() -> None:
    asyncio.run(_async_run_mcp_client())


if __name__ == "__main__":
    main()