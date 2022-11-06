from setuptools import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname),encoding='utf-8').read()

setup(name='GLRParser',
	version='0.3.25',
	description='A GLR Parser for Natural Language Processing and Translation',
	long_description=read("README.rst"),
	url='https://github.com/mdolgun/GLRParser',
	author='Mehmet Dolgun',
	author_email='m.dolgun@yahoo.com',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3.11',
	],
	keywords = 'NLP MachineTranslation Parser GLR Turkish',
	license='MIT',
	packages=['GLRParser'],
	package_data = { 'GLRParser': ['grm/*.grm', 'grm/*.grmc', 'grm/*.in.txt', 'grm/*.out.txt'] }
)
