"""
    Florgon Gatey SDK.
    Setup tools script.
"""

import os
from setuptools import setup, find_packages


# Read and pass all data from version file (module.)
version_file = {}
with open(
    os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "gatey_sdk", "__version__.py"
    ),
    "r",
    "utf-8",
) as f:
    exec(f.read(), version_file)

# Read whole readme file.
with open("README.md", "r", "utf-8") as f:
    readme = f.read()

classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
project_urls = {
    "Documentation": "https://github.com/florgon/gatey-sdk-py",
    "Source": "https://github.com/florgon/gatey-sdk-py",
}
setup(
    name=version_file["__title__"],
    version=version_file["__version__"],
    description=version_file["__description__"],
    long_description=readme,
    long_description_content_type="text/markdown",
    author=version_file["__author__"],
    author_email=version_file["__author_email__"],
    url=version_file["__url__"],
    packages=find_packages(),
    package_data={"": ["LICENSE"], "gatey_sdk": ["py.typed"]},
    package_dir={"gatey_sdk": "gatey_sdk"},
    include_package_data=True,
    license=version_file["__license__"],
    python_requires=">=3.10, <4",
    install_requires=[],
    classifiers=classifiers,
    project_urls=project_urls,
    zip_safe=False,
)
