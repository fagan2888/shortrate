# -*- coding: utf-8 -*-

#  shortrate
#  ------------
#  risk factor model library python style.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Copyright: 2016, 2017 Deutsche Postbank AG
#  Website: https://github.com/pbrisk/shortrate
#  License: APACHE Version 2 License (see LICENSE file)


import codecs
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='shortrate',
    description='risk factor model library python style.',
    version='0.2',
    author='Deutsche Postbank AG [pbrisk]',
    author_email='pbrisk_at_github@icloud.com',
    url='https://github.com/pbrisk/shortrate',
    bugtrack_url='https://github.com/pbrisk/shortrate/issues',
    license='Apache License 2.0',
    packages=['shortrate'],
    install_requires=['businessdate','timewave','dcf','scipy'],
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Education',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Utilities',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Localization',
    ],
)
