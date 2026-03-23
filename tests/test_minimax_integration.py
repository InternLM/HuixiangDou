"""Integration tests for MiniMax LLM provider.

These tests make real API calls to the MiniMax API.
They require MINIMAX_API_KEY to be set in the environment.

Run with: MINIMAX_API_KEY=your_key pytest tests/test_minimax_integration.py -v
"""
import os
import sys
import tempfile
import pytest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')
skip_no_key = pytest.mark.skipif(
    not MINIMAX_API_KEY,
    reason='MINIMAX_API_KEY not set'
)


@skip_no_key
class TestMiniMaxLLMIntegration:
    """Integration tests using real MiniMax API."""

    def _make_config(self, model='MiniMax-M1'):
        config_content = f"""
[llm]
[llm.server]
remote_type = "minimax"
remote_api_key = "{MINIMAX_API_KEY}"
remote_llm_max_text_length = 1000000
remote_llm_model = "{model}"
rpm = 500
tpm = 200000
"""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        f.write(config_content)
        f.flush()
        f.close()
        return f.name

    def test_chat_basic(self):
        """Test basic chat completion with MiniMax."""
        from huixiangdou.services.llm import LLM
        config_path = self._make_config()
        try:
            llm = LLM(config_path=config_path)
            result = asyncio.get_event_loop().run_until_complete(
                llm.chat(
                    prompt='What is 2+2? Reply with just the number.',
                    system_prompt='You are a helpful assistant. Be concise.',
                    max_tokens=1024,
                    timeout=60
                )
            )
            assert result is not None
            assert len(result) > 0
        finally:
            os.unlink(config_path)

    def test_chat_stream(self):
        """Test streaming chat completion with MiniMax."""
        from huixiangdou.services.llm import LLM
        config_path = self._make_config()
        try:
            llm = LLM(config_path=config_path)

            async def collect_stream():
                chunks = []
                async for chunk in llm.chat_stream(
                    prompt='Say hello.',
                    system_prompt='You are a helpful assistant. Be concise.',
                    max_tokens=1024,
                    timeout=60
                ):
                    chunks.append(chunk)
                return ''.join(chunks)

            result = asyncio.get_event_loop().run_until_complete(collect_stream())
            assert result is not None
            assert len(result) > 0
        finally:
            os.unlink(config_path)

    def test_chat_with_history(self):
        """Test chat with conversation history."""
        from huixiangdou.services.llm import LLM
        config_path = self._make_config()
        try:
            llm = LLM(config_path=config_path)
            history = [
                {'role': 'user', 'content': 'My name is Alice.'},
                {'role': 'assistant', 'content': 'Hello Alice! Nice to meet you.'},
            ]
            result = asyncio.get_event_loop().run_until_complete(
                llm.chat(
                    prompt='What is my name? Reply in one word.',
                    system_prompt='You are a helpful assistant. Be concise.',
                    history=history,
                    max_tokens=1024,
                    timeout=60
                )
            )
            assert result is not None
            assert len(result) > 0
            assert 'Alice' in result
        finally:
            os.unlink(config_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
