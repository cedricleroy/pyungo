from setuptools import setup
from os import path


HERE = path.abspath(path.dirname(__file__))


with open(path.join(HERE, 'README.rst')) as f:
    README = f.read()


setup(
    name='pyungo',
    version='0.3.0',
    description='Function dependencies resolution and execution',
    long_description=README,
    url='https://github.com/cedricleroy/pyungo',
    author='Cedric Leroy',
    author_email='cedie73@hotmail.fr',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='dag workflow function dependency',
    packages=['pyungo'],
)
