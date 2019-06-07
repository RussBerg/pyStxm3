'''
Created on Jul 7, 2016

@author: bergr
'''
#from distutils.core import setup
from setuptools import setup

setup(name='nxstxm_validate',
      version='1.0',
      description='Nexus NXstxm validation tool',
      author='Russ Berg',
      author_email='russ.berg@lightsource.ca',
      url='https://www.lightsource.ca',
      packages=['nxstxm_validate'],
      install_requires=[
          'nexpy',
          'xmltodict',
          'h5py'
      ],
     )