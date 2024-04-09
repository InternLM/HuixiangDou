from huixiangdou.service.llm_server_hybrid import HybridLLMServer, RPM, llm_serve
import time
import pytoml
from loguru import logger

def test_llm_backend():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    server = HybridLLMServer(llm_config=llm_config)

    _, error = server.generate_response(prompt='hello', history=[], backend='kimi')
    logger.error(error)
    assert len(error) > 0

    _, error = server.generate_response(prompt='hello', history=[], backend='deepseek')
    logger.error(error)
    assert len(error) > 0

    _, error = server.generate_response(prompt='hello', history=[], backend='zhipuai')
    logger.error(error)
    assert len(error) > 0

    _, error = server.generate_response(prompt='hello', history=[], backend='xi-api')
    logger.error(error)
    assert len(error) > 0

    # _, error = server.generate_response(prompt='hello', history=[], backend='alles-apin')
    # _, error = server.generate_response(prompt='hello', history=[], backend='puyu')

    
def test_rpm():
    rpm = RPM(30)

    for i in range(40):
        rpm.wait()
        print(i)

    time.sleep(5)

    for i in range(40):
        rpm.wait()
        print(i)

