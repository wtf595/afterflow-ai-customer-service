.PHONY: run test

run:
	python3 app.py --open

test:
	python3 -m unittest discover -s tests -v
