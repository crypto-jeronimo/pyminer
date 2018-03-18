#!/bin/bash

apt install -y make
make deps-android-gnuroot
CFLAGS="$CFLAGS" make install-android-gnuroot
