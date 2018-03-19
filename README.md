PyMiner
=======

This is a fork of Richard Moore's [nightminer](https://github.com/ricmoo/nightminer). It is a pure Python implementation of a Stratum CPU mining client.

[Jerônimo Cryptão](https://github.com/crypto-jeronimo) has extended the miner to support multiple algorithms, and performed further refactoring, optimizations and refinements.

Currently supported algorithms:
- `scrypt`: Scrypt
- `sha256d`: SHA256d
- `yescrypt`: Yescrypt

Installation
------------

For the Android instructions, please, refer to the corresponding section below.

For an easy install:
```
chmod +x ./build.sh ./deps.sh
sudo ./deps.sh
./build.sh
```

For installation on ARM-based devices, please replace `build.sh` and `deps.sh`
with `build-arm.sh` and `deps-arm.sh` in the lines above.

**Note:** Superuser privileges are _only_ required for installation of the `make`
package, in case it's not been installed on your system already.


Installation (Android)
----------------------

**Note:** PyMiner currently **does not** support dynamic CPU modification of current
utilization, based on physical measurements such as temperature. This means that
prolonged mining with your Android-based device may result in very high levels of
heat, and possible damage to your battery and/or device itself. Please, take extreme
caution as high temperatures are serious fire hazard.

In order to be able to install PyMiner on your Android-based device, you need to
obtain a suitable terminal emulation software from the official Google Play store.
Particularly, PyMiner has been successfully tested on the following apps:
- [Termux](https://play.google.com/store/apps/details?id=com.termux)
- [GNURoot Debian](https://play.google.com/store/apps/details?id=com.gnuroot.debian)

1. Termux
```
chmod +x ./build-android-termux.sh
./build-android-termux.sh
```

2. GNURoot Debian
```
chmod +x ./build-android-gnuroot.sh
./build-android-gnuroot.sh
```

Advanced Installation
---------------------

You can alternatively supply custom compilation arguments for the C bindings of
algorithms supported by PyMiner, via the `CFLAGS` environment variable (please,
note the double quotes), e.g.:
```
chmod +x ./build-arm.sh ./deps-arm.sh
sudo ./deps-arm.sh
CFLAGS="-O3 -funroll-loops -fomit-frame-pointer" sudo ./build-arm.sh
```

Usage
-----
```
    python pyminer.py [-h] [-o URL] [-u USERNAME] [-p PASSWORD]
                         [-O USERNAME:PASSWORD] [-a ALGO] [-B] [-q]
                         [-P] [-d] [-v]

    -o URL, --url=              stratum mining server url
    -u USERNAME, --user=        username for mining server
    -p PASSWORD, --pass=        password for mining server
    -O USER:PASS, --userpass=   username:password pair for mining server

    -a, --algo                  hashing algorithm to use for proof of work

    -B, --background            run in the background as a daemon

    -q, --quiet                 suppress non-errors
    -P, --dump-protocol         show all JSON-RPC chatter
    -d, --debug                 show extra debug information

    -h, --help                  show the help message and exit
    -v, --version               show program's version number and exit


    Example:
        python pyminer.py -o stratum+tcp://foobar.com:3333 -u user -p passwd
```

Please, note that for Android usage you need to change `python` to:
- GNURoot Debian: `python2.7`
- Termux: `python2`


Roadmap
-------

Next steps include but are not limited to:
- enable support for more algorithms: Yescrypt R8, Yescrypt R16, CryptoNight, Argon2d, Argon2i
- further optimization via Cython
- further optimization via automated compilation flag detection

Issues
------

Please, report any issues in the [Issues](LICENSE.txt) section.


License
-------

Please, see the [LICENSE](LICENSE.txt) document.


Donations
---------

If you have found this software useful and would like to support its future
development, please, feel free to donate:

- **BTC:** 1HKWV5t4KGUwybVHNUaaY9TXFSoBvoaSiP
- **ETH:** 0xF17e490B391E17BE2D14BFfaA831ab8966d2e689
- **LTC:** LNSEJzT8byYasZGd4f9c3DgtMbmexnXHdy
- **BCH:** 1AVXvPBrNdhTdwBN5VQT5LSHa7sEzMSia4
- **XEM:** NB3NDXRBOLEJLPT6MP6JAD4EZEOX5TFLDG3WR7JJ
- **MONA:** MPq54r8XTwtB2qmAeVqayy27ZCaPt845B6
- **KOTO:** k1GHJkvxLQocac94MFBbKAsdUvNbFdFWUyE
- **NEET:** NYaP7eEsDdALK5eHPZkYk1d8pBLyGvq9L1

After all, those morning cups of coffee need to come from somewhere, in order to
enable writing efficient code :)

Happy mining!
