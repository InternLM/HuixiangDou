import os
import re
import sys

from setuptools import find_packages, setup

pwd = os.path.dirname(__file__)
version_file = 'huixiangdou/version.py'


def readme():
    with open(os.path.join(pwd, 'README.md'), encoding='utf-8') as f:
        content = f.read()
    return content


def get_version():
    with open(os.path.join(pwd, version_file), 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']


def get_cuda_pkgs():
    arg_name = '--cuda='
    arg_value = None
    for arg in sys.argv[1:]:
        if arg.startswith(arg_name):
            arg_value = arg[len(arg_name):]
            sys.argv.remove(arg)
            break

    cuda_pkgs = []
    if arg_value == '11':
        cuda_pkgs = [
            'nvidia-nccl-cu11', 'nvidia-cuda-runtime-cu11',
            'nvidia-cublas-cu11'
        ]
    elif arg_value == '12':
        cuda_pkgs = [
            'nvidia-nccl-cu12', 'nvidia-cuda-runtime-cu12',
            'nvidia-cublas-cu12'
        ]
    return cuda_pkgs


cuda_pkgs = get_cuda_pkgs()


def parse_requirements(fname='requirements.txt', with_version=True):
    """Parse the package dependencies listed in a file but strips specific
    versioning information.

    Args:
        fname (str): path to the file
        with_version (bool, default=False): if True include version specs

    Returns:
        List[str]: list of requirements items

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    require_fpath = fname

    def parse_line(line):
        """Parse information from a line in a requirements text file."""
        if line.startswith('-r '):
            # Allow specifying requirements in other files
            target = line.split(' ')[1]
            for info in parse_require_file(target):
                yield info
        else:
            info = {'line': line}
            if line.startswith('-e '):
                info['package'] = line.split('#egg=')[1]
            elif '@git+' in line:
                info['package'] = line
            else:
                # Remove versioning from the package
                pat = '(' + '|'.join(['>=', '==', '>']) + ')'
                parts = re.split(pat, line, maxsplit=1)
                parts = [p.strip() for p in parts]

                info['package'] = parts[0]
                if len(parts) > 1:
                    op, rest = parts[1:]
                    if ';' in rest:
                        # Handle platform specific dependencies
                        # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                        version, platform_deps = map(str.strip,
                                                     rest.split(';'))
                        info['platform_deps'] = platform_deps
                    else:
                        version = rest  # NOQA
                    info['version'] = (op, version)
            yield info

    def parse_require_file(fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    for info in parse_line(line):
                        yield info

    def gen_packages_items():
        if os.path.exists(require_fpath):
            for info in parse_require_file(require_fpath):
                parts = [info['package']]
                if with_version and 'version' in info:
                    parts.extend(info['version'])
                if not sys.version.startswith('3.4'):
                    # apparently package_deps are broken in 3.4
                    platform_deps = info.get('platform_deps')
                    if platform_deps is not None:
                        parts.append(';' + platform_deps)
                item = ''.join(parts)
                yield item

    packages = list(gen_packages_items())
    packages += cuda_pkgs
    return packages


if __name__ == '__main__':
    huixiangdou_package_data = [
        'main.py', 'resource/bad_questions.json',
        'resource/good_questions.json', 'config.ini'
    ]
    setup(
        name='huixiangdou',
        version=get_version(),
        url='https://github.com/InternLM/huixiangdou',
        description=  # noqa E251
        'Overcoming Group Chat Scenarios with LLM-based Technical Assistance',  # noqa E501
        long_description=readme(),
        long_description_content_type='text/markdown',
        author='OpenMMLab',
        author_email='openmmlab@gmail.com',
        packages=find_packages(exclude=()),
        package_data={
            'huixiangdou': huixiangdou_package_data,
        },
        include_package_data=True,
        setup_requires=parse_requirements('requirements.txt'),
        install_requires=parse_requirements('requirements.txt'),
        classifiers=[
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Intended Audience :: Developers',
            'Intended Audience :: Education',
            'Intended Audience :: Science/Research',
        ],
        entry_points={'console_scripts': ['huixiangdou=huixiangdou.main:run']},
    )
