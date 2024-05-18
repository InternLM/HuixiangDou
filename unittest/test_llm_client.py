from huixiangdou.service.llm_client import ChatClient


def test_auto_fix():
    """test auto choose backend based on config."""
    remote_only_config = 'config-2G.ini'
    local_only_config = 'config.ini'
    full_config = 'config-advanced.ini'

    client = ChatClient(config_path=remote_only_config)
    real_backend, max_len = client.auto_fix(backend='local')
    assert real_backend != 'local'
    assert max_len >= 64000

    client = ChatClient(config_path=local_only_config)
    real_backend, max_len = client.auto_fix(backend='kimi')
    assert real_backend == 'local'

    client = ChatClient(config_path=full_config)
    real_backend, max_len = client.auto_fix(backend='local')
    assert real_backend == 'local'
    real_backend, max_len = client.auto_fix(backend='kimi')
    assert real_backend != 'local'
