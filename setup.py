import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gatey-sdk",
    version="0.0.0",
    author="Florgon Team and Contributors",
    author_email="support@florgon.space",
    description="Python client for Gatey (https://gatey.florgon.space)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    package_data={"gatey_sdk": ["py.typed"]},
    install_requires=[
        "requests>=2.28.1; python_version>='3.7'",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
