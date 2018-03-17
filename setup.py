from distutils.core import setup, Extension

scrypt_module = Extension('scrypt',
                               sources = ['scryptmodule.c',
                                          'scrypt.c'],
                               include_dirs=['.'])

setup(name='scrypt',
       version='1.0',
       description='Bindings for scrypt proof of work',
       ext_modules=[scrypt_module])
