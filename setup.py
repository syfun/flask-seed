"""
Flask-Seed
-------------

This is the description for that library
"""
from setuptools import setup


setup(
    name='Flask-Seed',
    version='0.1',
    url='http://example.com/flask-seed/',
    license='MIT',
    author='syfun',
    author_email='sunyu418@gmail.com',
    description='Flask simple seed with mongodb.',
    long_description=__doc__,
    py_modules=['flask_seed'],
    # if you would be using a package instead use packages instead
    # of py_modules:
    # packages=['flask_seed'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'Flask-PyMongo',
        'Flask-Script',
        'gevent'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)