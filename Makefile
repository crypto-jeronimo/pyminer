deps:
	sudo apt-get install -y python2.7-dev

install:
	python setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

deps-arm:
	pkg instll -y python2-dev

install-arm:
	PLATFORM=arm python2 setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

clean:
	rm -f $(shell pwd)/scrypt.so
