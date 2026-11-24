# StudySpace developer commands.
# These work with Python 3.12 and the standard library only.

PYTHON ?= python
PORT ?= 8000
DB ?= data/studyspace.db

.PHONY: run test clean

run:
	$(PYTHON) -m studyspace --port $(PORT) --db $(DB)

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	rm -f data/studyspace.db
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
