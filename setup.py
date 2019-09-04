from setuptools import setup, Extension


setup (name = 'methodfinder',
       version = '0.0.2',
       description = 'For when you know some procedure must already exist, and you want to quickly find its name',
       author = 'William Emerison Six',
       author_email = 'billsix@gmail.com',
       url = 'https://github.com/billsix/methodfinder',
       keywords = "methodfinder",
       license = "MIT",
       packages=['methodfinder'],
       package_dir={'methodfinder': 'src/methodfinder'},
       classifiers=[
           "Development Status :: 3 - Alpha",
           "Topic :: Utilities",
           "License :: OSI Approved :: MIT License",
       ],
       long_description = '''
For when you know some procedure must already exist, and you want to quickly find its name.  Inspired from Smalltalk 80.
''')
