install:
	CFLAGS="$(CFLAGS)" python setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

install-arm:
	echo "cfl=$(CFLAGS)"
	CFLAGS="$(CFLAGS)" PLATFORM=arm python setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

install-android-termux:
	CFLAGS="$(CFLAGS)" python2 setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

install-android-gnuroot:
	CFLAGS="$(CFLAGS)" python2.7 setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

clean:
	rm -f $(shell pwd)/*.so
