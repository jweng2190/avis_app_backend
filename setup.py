from setuptools import find_packages
from setuptools import setup


setup(
    name="avis_app",
    version="1.0.0",
    url="https://flask.palletsprojects.com/tutorial/",
    license="BSD",
    maintainer="Pallets team",
    maintainer_email="contact@palletsprojects.com",
    description="The basic blog app built in the Flask tutorial.",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask", 'mysql'],
    extras_require={"test": ["pytest", "coverage"]},
)