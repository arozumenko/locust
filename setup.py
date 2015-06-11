from sys import platform
from setuptools import setup

install_requires = [
    'psutil',
    'configobj',
    'apscheduler',
    'Flask>=0.10',
    'flask_restful',
    'iptools',
    'gevent',
    'requests',
    'supervisor',
    'netifaces'
]

if any(name in platform for name in ['win32']):
    install_requires += ['winpaths', 'win32service', 'win32service',
                         'win32event', 'winerror', 'servicemanager',
                         'win32serviceutil']

version = '1.0a'

setup(name='locust',
      version=version,
      packages=[
          'locust',
          'locust.common',
          'locust.serviceutils'],
      install_requires=install_requires,
      entry_points={
          'console_scripts': ['locust = locust.cli:main']
      },
      # Metadata.
      description='Crossplatform failure testing tool for distributed systems',
      author='Artem Rozumenko',
      author_email='artyom.rozumenko@gmail.com',
      license='Apache Software License')
