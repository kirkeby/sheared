H2PY=python $(shell pwd)/bin/h2py.py

all: test/http-docroot/all.tar.gz

clean:
	rm -rf build/
	find . -name \*.py[oc] | rm -f

#sheared/python/stropts.py: /usr/include/bits/stropts.h
#	cd $(dir $@) ; $(H2PY) $<

test: tests/http-docroot/all.tar.gz
	./bin/test
	touch test

test/http-docroot/all.tar.gz: $(addprefix test/http-docroot/,hello.py hello.txt index.html)
	tar c $^ | gzip -9 > $@
