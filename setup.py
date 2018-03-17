import os
from distutils.core import setup, Extension

args = ['-O3']
if os.environ.get('PLATFORM', '') == 'ARM':
    args += ['-funroll-loops', '-fomit-frame-pointer']

scrypt_module = Extension('scrypt',
                           sources = ['scryptmodule.c',
                                      'scrypt.c'],
                           extra_compile_args=args,
                           include_dirs=['.'])

setup(name='scrypt',
       version='1.0',
       description='Bindings for scrypt proof of work',
       ext_modules=[scrypt_module])
