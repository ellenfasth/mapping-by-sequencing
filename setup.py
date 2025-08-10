from setuptools import setup, find_packages

setup(
    name="mapping_by_sequencing",
    version="1.0.0",
    description="Mapping-by-sequencing Pipeline Package",
    author="Pipeline Development Team",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "pyyaml",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "mbs=mapping_by_sequencing.pipeline.run_manager:main",
        ],
    },
)
