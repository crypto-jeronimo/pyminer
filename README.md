PyMiner
=======

This is a fork of Richard Moore's [nightminer](https://github.com/ricmoo/nightminer). It is a very simple pure Python implementation of a Stratum CPU mining client.

Currently supported algorithms:
- Scrypt
- Yescrypt

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
