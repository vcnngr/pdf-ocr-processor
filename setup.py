#!/usr/bin/env python3
"""
PDF OCR Processor - Setup per installazione locale
"""

from setuptools import setup, find_packages
import os

# Leggi README per long_description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Leggi requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pdf-ocr-processor",
    version="1.0.0",
    author="PDF OCR Team",
    author_email="team@pdf-ocr-processor.com",
    description="Trasforma qualsiasi PDF in documento ricercabile e ottimizzato",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/pdf-ocr-processor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Text Processing :: General",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "black>=23.12.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "api": [
            "flask>=3.0.0",
            "gunicorn>=21.2.0",
        ],
        "monitoring": [
            "psutil>=5.9.7",
            "prometheus-client>=0.19.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pdf-ocr-process=scripts.pdf_processor:main",
            "pdf-ocr-api=scripts.api_wrapper:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.sh"],
    },
    zip_safe=False,
)
