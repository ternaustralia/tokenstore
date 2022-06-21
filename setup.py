import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as f:
    README = f.read()

requires = [
    "Flask",
    "Flask-Cors",
    "Flask-Migrate",
    "flask_tern",
]

tests_require = [
    line.strip()
    for line in open(os.path.join(here, "requirements-test.txt"))
    if not line.startswith("#")
]

docs_require = [
    "mistune==0.8.4",
    "sphinx",
    "sphinx-autobuild",
    "sphinxcontrib_openapi",
    "sphinx-rtd-theme",
]

setup(
    name="tokenstore",
    use_scm_version={
        # put a version file into module on build to simplify pkg version discovery
        "write_to": "src/tokenstore/version.py",
        "fallback_version": "0.0.0.dev0",
    },
    setup_requires=["setuptools_scm"],
    description="tokenstore",
    long_description=README,
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Flask",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: Apache Software License",
    ],
    author="",
    author_email="",
    url="",
    keywords="web flask",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    extras_require={
        "testing": tests_require,
        "docs": docs_require,
    },
    install_requires=requires,
    entry_points={
        # "paste.app.factory": [
        #     "main = tokenstore:main",
        # ],
    },
)
