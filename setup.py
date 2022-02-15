from setuptools import setup

from smot.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

# Read the requirements from the requirements.txt file
with open("requirements.txt", "r") as fh:
    requirements = [r.strip() for r in fh.readlines()]

setup(
    name="smot",
    version=__version__,
    description="simple manipulation of trees",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flu-crew/smot",
    author="Zebulun Arendsee",
    author_email="zebulun.arendsee@usda.gov",
    packages=["smot"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["smot=smot.main:main"]},
    install_requires=requirements,
    package_data={"smot": ["py.typed"]},
    py_modules=["smot"],
    zip_safe=False,
)
