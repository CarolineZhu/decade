from setuptools import setup, find_packages

setup(
    name = "decade",
    version = "0.0.9",
    keywords = ("pip", "decade", "rzhu"),
    description = "debug configurator sdk",
    long_description = "Pycharm remote debug auto configurator sdk",
    license = "Splunk Licence",

    url = "https://github.com/CarolineZhu/decade",
    author = "rzhu",
    author_email = "rzhu@splunk.com",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = ["paramiko"],
    entry_points = {
        'console_scripts': ['decade = decade.localentry:main']
    }
)
