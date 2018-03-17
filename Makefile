scrypt:
	python setup.py build_ext --inplace
	rm -rf $(shell pwd)/build

clean:
	rm -f $(shell pwd)/scrypt.so
