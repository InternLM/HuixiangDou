from huixiangdou.service.llm_server_hybrid import RPM, TPM

def test_rpm():
    rpm = RPM(30)

    for i in range(40):
        rpm.wait()
        print(i)

    time.sleep(5)

    for i in range(40):
        rpm.wait()
        print(i)

def test_tpm():
    tpm = TPM(2000)

    for i in range(20):
        tpm.wait(silent=False, token_count=150)
        print(i)

if __name__ == '__main__':
    test_tpm()