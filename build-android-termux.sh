#!/bin/bash

pkg install -y make
make deps-android-termux
make install-android-termux
