from setuptools import setup, find_packages

setup(
    name = "decade",
    version = "0.0.1",
    keywords = ("pip", "decade", "debug-auto-config", "rzhu"),
    description = "debug configurator sdk",
    long_description = "Pycharm remote debug auto configurator sdk",
    license = "Splunk Licence",

    url = "http://xiaoh.me",
    author = "rzhu",
    author_email = "rzhu@splunk.com",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = ["paramiko"]
)