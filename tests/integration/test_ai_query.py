import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from production_mcp_integration import ConstructionMCPEngine, MCPRequest, RequestType  # type: ignore


RUN_AI_TESTS = os.getenv("RUN_AI_QUERY_TESTS") == "1" or os.getenv("RUN_INTEGRATION_TESTS") == "1"


async def _async_test_ai_query() -> None:
    engine = ConstructionMCPEngine()
    await engine.initialize()

    request = MCPRequest(
        id='test-001',
        type=RequestType.AI_QUERY,
        query='What are the current projects and their clients?',
        parameters={},
        timestamp=datetime.now(),
    )

    response = await engine._handle_ai_query(request)
    print("🤖 AI Response:")
    print(response.get('ai_response', 'No response'))


@pytest.mark.skipif(not RUN_AI_TESTS, reason="AI query integration test disabled. Set RUN_AI_QUERY_TESTS=1 to enable.")
def test_ai_query() -> None:
    asyncio.run(_async_test_ai_query())
