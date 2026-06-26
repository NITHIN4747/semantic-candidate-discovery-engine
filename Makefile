# TrioLogic SRE Automation Protocol
.PHONY: install test run-ui bench clean

install:
	pip install -r requirements.txt

test:
	python -m unittest discover tests/

run-ui:
	streamlit run app.py

# Simulates the sandbox evaluation
bench:
	python rank.py --candidates data/candidates.jsonl --out submission.csv

clean:
	rm -rf __pycache__ .pytest_cache
	rm -f submission.csv
