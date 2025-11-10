"""
Setup configuration for Quantum-Resistant Cryptography Performance Simulator.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="quantum-crypto-simulator",
    version="1.0.0",
    author="Bhaskar Datta",
    author_email="bhaskar@example.com",
    description="Interactive benchmarking tool for comparing Classical, Post-Quantum, and Hybrid cryptographic protocols",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bhaskardatta/Quantum-performance-simulator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Flask",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "quantum-crypto-sim=web_dashboard:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.html", "static/*.css", "static/*.js"],
    },
)
