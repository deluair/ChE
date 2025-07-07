from setuptools import setup, find_packages

setup(
    name='nexus',
    version='0.1.0',
    packages=find_packages(),
    description='A digital twin simulation for multi-scale chemical process optimization.',
    author='Cascade AI',
    install_requires=[
        'numpy',
        'pandas',
        'scipy',
        'matplotlib',
        'CoolProp',
        'seaborn'
    ],
)
