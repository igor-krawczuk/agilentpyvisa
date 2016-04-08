from distutils.core import setup
setup(
    name = "agilentpyvisa",
    packages = ["agilentpyvisa"],
    version = "0.0.1",
    description = "Intuitive agilent tester control via VISA",
    author = "Igor Krawczuk",
    license="AGPLv3",
    author_email = "igor@krawczuk.eu",
    url = "https://github.com/wojcech/agilentpyvisa",
    download_url = "https://github.com/wojcech/agilentpyvisa/archive/master.zip",
    keywords = ["VISA", "agilent", "tester"],
    instal_requires = [
    "pyvisa",
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 1 - Planning",
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering",
        ],
    long_description = """\
Intuitive agilent tester control via VISA
-------------------------------------

Provides Enums, namedtuples and Interface classes for readbale testing scripts.

Currently supports:

- B1500

Available for python3 only.
"""
)
