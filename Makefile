test: tests/http-docroot/all.tar.gz
	./bin/test
	touch test

tests/http-docroot/all.tar.gz: $(addprefix tests/http-docroot/,hello.py hello.txt index.html)
	tar c $^ | gzip -9 > $@
