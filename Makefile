.PHONY: default clean test

default: test

clean:
	find . -name '*.pyc' -delete
	find . -depth -name __pycache__ -delete

test:
	./test
