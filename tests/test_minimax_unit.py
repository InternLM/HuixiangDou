"""Unit tests for MiniMax LLM provider integration."""
import os
import sys
import json
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from huixiangdou.services.llm import backend2url, backend2model, Backend, LLM


class TestMiniMaxBackendRegistry:
    """Tests for MiniMax entries in backend registries."""

    def test_minimax_url_registered(self):
        """MiniMax base URL should be in backend2url."""
        assert 'minimax' in backend2url
        assert backend2url['minimax'] == 'https://api.minimax.io/v1'

    def test_minimax_default_model_registered(self):
        """MiniMax default model should be in backend2model."""
        assert 'minimax' in backend2model
        assert backend2model['minimax'] == 'MiniMax-M1'

    def test_backend2url_has_all_providers(self):
        """All documented providers should be in backend2url."""
        expected = ['kimi', 'step', 'xi-api', 'deepseek', 'zhipuai',
                    'siliconcloud', 'local', 'vllm', 'ppio', 'internlm', 'minimax']
        for provider in expected:
            assert provider in backend2url, f'{provider} missing from backend2url'


class TestMiniMaxBackendInit:
    """Tests for Backend class with MiniMax config."""

    def test_backend_minimax_auto_url(self):
        """Backend should auto-resolve MiniMax base URL."""
        data = {
            'remote_api_key': 'test-key',
            'remote_type': 'minimax',
            'remote_llm_max_text_length': 1000000,
            'remote_llm_model': 'MiniMax-M1',
        }
        backend = Backend(name='minimax', data=data)
        assert backend.base_url == 'https://api.minimax.io/v1'
        assert backend.api_key == 'test-key'
        assert backend.model == 'MiniMax-M1'

    def test_backend_minimax_custom_url(self):
        """Backend should use custom base_url if provided."""
        data = {
            'remote_api_key': 'test-key',
            'remote_type': 'minimax',
            'remote_llm_max_text_length': 32000,
            'remote_llm_model': 'MiniMax-M1',
            'base_url': 'https://custom.proxy.com/v1',
        }
        backend = Backend(name='minimax', data=data)
        assert backend.base_url == 'https://custom.proxy.com/v1'

    def test_backend_minimax_max_token_calculation(self):
        """Backend should calculate max_token_size correctly."""
        data = {
            'remote_api_key': 'test-key',
            'remote_type': 'minimax',
            'remote_llm_max_text_length': 1000000,
            'remote_llm_model': 'MiniMax-M1',
        }
        backend = Backend(name='minimax', data=data)
        assert backend.max_token_size == 1000000 - 4096

    def test_backend_minimax_default_rpm_tpm(self):
        """Backend should use default RPM/TPM if not specified."""
        data = {
            'remote_api_key': 'test-key',
            'remote_type': 'minimax',
            'remote_llm_max_text_length': 32000,
            'remote_llm_model': 'MiniMax-M1',
        }
        backend = Backend(name='minimax', data=data)
        assert backend.rpm is not None
        assert backend.tpm is not None

    def test_backend_minimax_custom_rpm_tpm(self):
        """Backend should accept custom RPM/TPM."""
        data = {
            'remote_api_key': 'test-key',
            'remote_type': 'minimax',
            'remote_llm_max_text_length': 32000,
            'remote_llm_model': 'MiniMax-M1',
            'rpm': 100,
            'tpm': 80000,
        }
        backend = Backend(name='minimax', data=data)
        # RPM/TPM are wrappers, just check they were created
        assert backend.rpm is not None
        assert backend.tpm is not None

    def test_backend_minimax_jsonify(self):
        """Backend jsonify should return expected format."""
        data = {
            'remote_api_key': 'test-key',
            'remote_type': 'minimax',
            'remote_llm_max_text_length': 32000,
            'remote_llm_model': 'MiniMax-M1',
        }
        backend = Backend(name='minimax', data=data)
        result = backend.jsonify()
        assert result['api_key'] == 'minimax'
        assert result['model'] == 'MiniMax-M1'


class TestMiniMaxModelSelection:
    """Tests for choose_model() with MiniMax backend."""

    def _make_llm_with_minimax(self, model='auto'):
        """Helper to create LLM instance with MiniMax config."""
        config_content = f"""
[llm]
[llm.server]
remote_type = "minimax"
remote_api_key = "test-key"
remote_llm_max_text_length = 1000000
remote_llm_model = "{model}"
rpm = 500
tpm = 200000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                llm = LLM(config_path=f.name)
                return llm
            finally:
                os.unlink(f.name)

    def test_choose_model_auto_small_input(self):
        """Auto mode should select MiniMax-M1 for small input."""
        llm = self._make_llm_with_minimax(model='auto')
        backend = llm.backends['minimax']
        model = llm.choose_model(backend, token_size=1000)
        assert model == 'MiniMax-M1'

    def test_choose_model_auto_medium_input(self):
        """Auto mode should select MiniMax-M1 for medium input."""
        llm = self._make_llm_with_minimax(model='auto')
        backend = llm.backends['minimax']
        model = llm.choose_model(backend, token_size=100000)
        assert model == 'MiniMax-M1'

    def test_choose_model_auto_large_input(self):
        """Auto mode should select MiniMax-M1 for large input within 1M."""
        llm = self._make_llm_with_minimax(model='auto')
        backend = llm.backends['minimax']
        model = llm.choose_model(backend, token_size=500000)
        assert model == 'MiniMax-M1'

    def test_choose_model_auto_exceeds_limit(self):
        """Auto mode should raise ValueError when input exceeds 1M."""
        llm = self._make_llm_with_minimax(model='auto')
        backend = llm.backends['minimax']
        with pytest.raises(ValueError, match='1M'):
            llm.choose_model(backend, token_size=1000001)

    def test_choose_model_explicit(self):
        """Explicit model name should be used as-is."""
        llm = self._make_llm_with_minimax(model='MiniMax-M1')
        backend = llm.backends['minimax']
        model = llm.choose_model(backend, token_size=5000)
        assert model == 'MiniMax-M1'

    def test_choose_model_empty_uses_default(self):
        """Empty model should fall back to backend2model default."""
        llm = self._make_llm_with_minimax(model='')
        backend = llm.backends['minimax']
        # Empty model but not 'auto', falls to backend2model lookup
        model = llm.choose_model(backend, token_size=5000)
        assert model == 'MiniMax-M1'


class TestMiniMaxLLMInit:
    """Tests for LLM initialization with MiniMax config."""

    def test_llm_init_minimax(self):
        """LLM should initialize correctly with MiniMax config."""
        config_content = """
[llm]
[llm.server]
remote_type = "minimax"
remote_api_key = "test-api-key"
remote_llm_max_text_length = 1000000
remote_llm_model = "MiniMax-M1"
rpm = 500
tpm = 200000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                llm = LLM(config_path=f.name)
                assert 'minimax' in llm.backends
                assert llm.backends['minimax'].base_url == 'https://api.minimax.io/v1'
                assert llm.backends['minimax'].model == 'MiniMax-M1'
            finally:
                os.unlink(f.name)

    def test_llm_default_model_info_minimax(self):
        """default_model_info should return MiniMax info."""
        config_content = """
[llm]
[llm.server]
remote_type = "minimax"
remote_api_key = "test-api-key"
remote_llm_max_text_length = 32000
remote_llm_model = "MiniMax-M1"
rpm = 500
tpm = 200000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(config_content)
            f.flush()
            try:
                llm = LLM(config_path=f.name)
                info = llm.default_model_info()
                assert info['api_key'] == 'minimax'
                assert info['model'] == 'MiniMax-M1'
            finally:
                os.unlink(f.name)


class TestMiniMaxConfigFiles:
    """Tests for MiniMax references in config files."""

    def test_config_ini_mentions_minimax(self):
        """config.ini should document MiniMax as supported provider."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        with open(config_path) as f:
            content = f.read()
        assert 'minimax' in content.lower()

    def test_readme_mentions_minimax(self):
        """README.md should list MiniMax as supported LLM."""
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        with open(readme_path) as f:
            content = f.read()
        assert 'MiniMax' in content

    def test_readme_zh_mentions_minimax(self):
        """README_zh.md should list MiniMax as supported LLM."""
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README_zh.md')
        with open(readme_path) as f:
            content = f.read()
        assert 'MiniMax' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
