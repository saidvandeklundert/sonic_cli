from setuptools import setup, find_packages

setup(
    name="sonic-cli",
    version="0.1.0",
    packages=find_packages(),
    # package_dir={"": "sonic_cli"},
    # Metadata
    author="Said van de Klundert",
    author_email="said.van.de.klundert@gmail.com",
    description="Several additions to the SONiC CLI.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/saidvandeklundert/sonic_cli",
    install_requires=[
        "redis>=5.0.6",
        "psutil>=5.9.0",
    ],
    # Entry points
    entry_points={
        "console_scripts": [
            "sonic-cli=sonic_cli.main:main",  # Assumes you have a main.py with a main() function
        ],
    },
    # Classifiers
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Python version requirement
    python_requires=">=3.9",
)
