PyMiner
=======

This is a fork of Richard Moore's [nightminer](https://github.com/ricmoo/nightminer). It is a pure Python implementation of a Stratum CPU mining client.

[Jerônimo Cryptão](https://github.com/crypto-jeronimo) has extended the miner to support multiple algorithms, and performed further refactoring, optimizations and refinements.

Currently supported algorithms:
- Scrypt
- Yescrypt

Installation Instructions
-------------------------

For the Android instructions, please, refer to the corresponding section below.

First, you need to install all required dependencies:
```
sudo apt-get -y install make
```

Then, simply run

Installation Instructions (Android)
-----------------------------------

[Termux](https://play.google.com/store/apps/details?id=com.termux) from the Google Play store.

Command Line Interface
----------------------
```
    python pyminer.py [-h] [-o URL] [-u USERNAME] [-p PASSWORD]
                         [-O USERNAME:PASSWORD] [-a {scrypt,yescrypt}] [-B] [-q]
                         [-P] [-d] [-v]

    -o URL, --url=              stratum mining server url
    -u USERNAME, --user=        username for mining server
    -p PASSWORD, --pass=        password for mining server
    -O USER:PASS, --userpass=   username:password pair for mining server

    -a, --algo                  hashing algorithm to use for proof of work (scrypt, sha256d)

    -B, --background            run in the background as a daemon

    -q, --quiet                 suppress non-errors
    -P, --dump-protocol         show all JSON-RPC chatter
    -d, --debug                 show extra debug information

    -h, --help                  show the help message and exit
    -v, --version               show program's version number and exit


    Example:
        python pyminer.py -o stratum+tcp://foobar.com:3333 -u user -p passwd
```

License
-------

