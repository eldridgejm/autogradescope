from setuptools import setup, find_packages

setup(
    name="autogradescope",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["pytest", "click", "rich"],
    package_data={
        "autogradescope": ["template/"],
    },
)
