# Check `huixiangdou.service.main` works
import os
import time

from loguru import logger


def command(txt: str):
    """Executes a shell command and returns its output.

    Args:
        txt (str): Command to be executed in the shell.

    Returns:
        str: Output of the shell command execution.
    """
    logger.debug('cmd: {}'.format(txt))
    cmd = os.popen(txt)
    return cmd.read().rstrip().lstrip()


def has_new_commit():
    command('git pull')
    filename = 'commit.id'
    commit_id = command('git log -1 HEAD | head -n 1 ')
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write(commit_id)
        return True

    old_id = ''
    with open(filename) as f:
        old_id = f.read()

    if old_id != commit_id:
        with open(filename, 'w') as f:
            f.write(commit_id)
        return True

    return False


def run():
    actions = {
        'llm_server_hybrid':
        'python3 -m huixiangdou.service.llm_server_hybrid --config_path .github/scripts/config-ci.ini  --unittest',  # noqa E501
        'feature_store':
        'python3 -m huixiangdou.service.feature_store --config_path .github/scripts/config-ci.ini',  # noqa E501
        'main':
        'python3 -m huixiangdou.main --standalone --config_path .github/scripts/config-ci.ini'  # noqa E501
    }

    reports = ['HuixiangDou daily smoke:']
    for action, cmd in actions.items():
        log = command(cmd)
        if 'ERROR' in log or 'ConnectionResetError' in log:
            reports.append(f'*{action}, failed')
        else:
            reports.append(f'*{action}, passed')
    return reports


def main():
    HISOTRY = '/home/khj/github-lark/history.txt'

    while True:
        if has_new_commit():
            reports = run()
            report_text = '\n'.join(reports)
            with open(HISOTRY, 'a') as f:
                f.write(report_text)
        else:
            logger.info('no update, skip.')
        time.sleep(3600 * 24)


if __name__ == '__main__':
    main()
