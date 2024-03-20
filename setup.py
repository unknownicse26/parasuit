from setuptools import find_packages
from setuptools import setup

from parasuit import __version__


setup(
    name='parasuit',
    version=__version__,
    description='Parasuit: Full Automation of External Parameter Tuning for Symbolic Execution',
    python_version='>=3.9',
    packages=find_packages(include=('parasuit', 'parasuit.*')),
    include_package_data=True,
    setup_requires=[],
    install_requires=[
        'scikit-learn',
        'gensim'
    ],
    dependency_links=[],
    entry_points={
        'console_scripts': [
            'parasuit=parasuit.bin:main',
        ]
    }
)
