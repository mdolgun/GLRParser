from setuptools import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname),encoding='utf-8').read()
	
setup(name='GLRParser',
	version='0.2.1',
	description='A GLR Parser for Natural Language Processing and Translation',
	long_description=read("README.rst"),
	url='https://github.com/mdolgun/GLRParser',
	author='Mehmet Dolgun',
	author_email='m.dolgun@yahoo.com',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3.6'
	],
	keywords = 'NLP MachineTranslation Parser GLR Turkish',
	license='MIT',
	packages=['GLRParser'],
	package_data = { 'GLRParser': ['*.grm'] }
)