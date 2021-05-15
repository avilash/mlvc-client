import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="MLVC",
    packages=setuptools.find_packages(),
    version="0.0.1",
    license='MIT',
    author="Avilash Kumar",
    author_email="avilashkumar4@gmail.com",
    description="MLVC Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/avilash/mlvc-client",
    download_url='https://github.com/avilash/mlvc-client/tarball/main',
    keywords=[],
    install_requires=[

    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
    ],
    include_package_data=True
)
