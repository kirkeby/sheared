H2PY=python $(shell pwd)/bin/h2py.py

all: sheared/python/stropts.py

sheared/python/stropts.py: /usr/include/bits/stropts.h
	cd $(dir $@) ; $(H2PY) $<

test: tests/http-docroot/all.tar.gz
	./bin/test
	touch test

tests/http-docroot/all.tar.gz: $(addprefix tests/http-docroot/,hello.py hello.txt index.html)
	tar c $^ | gzip -9 > $@
