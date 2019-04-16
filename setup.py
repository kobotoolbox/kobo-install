from distutils.core import setup
from setuptools import find_packages


setup(
    name='KoBoInstall',
    version='68421f4',
    packages=find_packages(exclude=['tests']),  # Include all the python modules except `tests`,
    url='https://github.com/kobotoolbox/kobo-install/',
    license='',
    author='KoBoToolbox',
    author_email='',
    description='Installer for KoBoToolbox'
)
