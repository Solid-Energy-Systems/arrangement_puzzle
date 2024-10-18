from setuptools import setup, find_packages

setup(
    name='arrangement_puzzle',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'tqdm',  # list of dependencies if any
    ],
    author='Adam Atanas',
    author_email='adam.atanas@ses.ai',
    description='A generator for a particular type of word puzzle, for use in RL and activation studies of reasoning LLM agents.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Solid-Energy-Systems/arrangement_puzzle',
    python_requires='>=3.6',
)
