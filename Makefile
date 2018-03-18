deps:
	sudo apt-get install -y python2.7-dev

deps-android-gnuroot:
	apt install -y python2.7-dev

deps-android-termux:
	pkg instll -y python2-dev

install:
	python setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

install-arm:
	PLATFORM=arm python setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

install-android-termux:
	python2.7 setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

install-android-termux:
	PLATFORM=arm python2 setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

clean:
	rm -f $(shell pwd)/*.so
