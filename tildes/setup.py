"""Extremely minimal setup.py to support pip install -e."""

from setuptools import find_packages, setup


setup(
    name="tildes",
    version="0.1",
    packages=find_packages(),
    entry_points="""
    [paste.app_factory]
    main = tildes:main
    """,
)
