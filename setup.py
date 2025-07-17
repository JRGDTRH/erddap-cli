from setuptools import setup, find_packages

setup(
    name="erddap-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "erddapy",
        "pandas",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "erddap-cli=erddap_cli.cli:main",
        ]
    },
)