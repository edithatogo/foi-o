.PHONY: validate test

validate:
	python tests/validate_repo.py

test:
	pytest -q
