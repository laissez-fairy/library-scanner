import pytest
import asyncio
import main
import io
from telegram.ext import ConversationHandler

class MockContext:
    def __init__(self, bot):
        self.user_data = {}
        self.bot = bot

@pytest.mark.asyncio
class MockBot:
    async def send_message(self, user_id, message, **kwargs):
        return 0

mock_bot = MockBot()
mock_context = MockContext(mock_bot)

@pytest.mark.asyncio
async def test_request():
    assert await main.requestfromcode(1476, 0, mock_context) == 0

@pytest.mark.asyncio
async def test_request_2():
    assert await main.requestfromcode(9780749397050, 0, mock_context) == {'title': 'The Name of the Rose',
                                                                          'author': 'Umberto Eco'}