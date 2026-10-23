from setuptools import setup, find_packages

setup(
    name="strands-sentry-ops",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["cli"],
    entry_points={
        "console_scripts": [
            "sentry-ops=cli:main",
        ],
    },
)
