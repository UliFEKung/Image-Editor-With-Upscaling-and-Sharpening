"""
Setup file for Image Editor application.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Image Editor With Upscaling and Sharpening",
    version="1.0.0",
    author="UliFEKung and Team",
    author_email="peepee12213443@gmail.com",
    description="A simple image editor with upscaling and sharpening capabilities.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=9.0.0",
        "tkinterdnd2>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "image-editor=main:main",
        ],
    },
)
