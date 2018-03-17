import os
from distutils.core import setup, Extension


scrypt_module = Extension('scrypt',
                           sources = ['scryptmodule.c',
                                      'scrypt.c'],
                           extra_compile_args=[
                                '-O3', '-funroll-loops', '-fomit-frame-pointer']
                                if os.environ.get('PLATFORM', '') == 'arm'
                                else ['-O3'],
                           include_dirs=['.'])

setup(name='scrypt',
       version='1.0',
       description='Bindings for scrypt proof of work',
       ext_modules=[scrypt_module])
