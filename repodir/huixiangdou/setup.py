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


def read_requirements():
    lines = []
    with open('requirements.txt', 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            if 'textract' in line:
                continue
            if len(line) > 0:
                lines.append(line)
    return lines


install_packages = read_requirements()

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
        setup_requires=install_packages,
        install_requires=install_packages,
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
