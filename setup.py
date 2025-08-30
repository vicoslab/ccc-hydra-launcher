from setuptools import setup, find_namespace_packages
import os

def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setup(
    name='ccc-hydra-launcher',
    version='0.2.0',
    description='Hydra launcher plugin for Conda Compute Cluster',
    long_description=read('README.md'),
    author='Domen Tabernik',
    author_email='domen.tabernik@fri.uni-lj.si',
    packages=find_namespace_packages(include=["hydra_plugins.*"]),
    include_package_data=True,
    entry_points={
        'hydra.launcher': ['ccc = hydra_plugins.hydra_ccc_launcher.conf:CCCLauncherConfig'],
        "hydra.plugins": [
            "hydra_ccc_launcher = hydra_plugins.hydra_ccc_launcher.ccc_launcher",
        ]        
    },
    install_requires=['psutil', 'hydra-core>=1.0'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: Hydra',
    ],
)
