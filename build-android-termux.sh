#!/bin/bash

pkg install -y make
make deps-android-termux
CFLAGS="$CFLAGS" make install-android-termux
