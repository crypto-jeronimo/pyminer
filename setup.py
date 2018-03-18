import os
from setuptools import setup, Extension


CFLAGS = os.environ.get('CFLAGS', '').strip()

if CFLAGS:
  extra_compile_args = CFLAGS.split()
else:
  extra_compile_args = (
                        ['-O3', '-funroll-loops', '-fomit-frame-pointer']
                        if os.environ.get('PLATFORM', '') == 'arm'
                        else ['-O3'])

scrypt_module = Extension('scrypt',
                          sources=['./algos/scrypt/scryptmodule.c',
                                    './algos/scrypt/scrypt.c'],
                          extra_compile_args=extra_compile_args,
                          include_dirs=['./algos/scrypt'])

yescrypt_module = Extension('yescrypt',
                            sources=['./algos/yescrypt/yescrypt.c'],
                            extra_compile_args=extra_compile_args,
                            include_dirs=['./algos/yescrypt'])

setup(name='scrypt',
      version='1.0',
      description='Bindings for scrypt proof of work',
      ext_modules=[scrypt_module])

setup(name='yescrypt',
      version='1.0',
      description='Bindings for yescrypt proof of work',
      ext_modules=[yescrypt_module])
