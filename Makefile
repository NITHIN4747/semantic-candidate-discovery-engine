# TrioLogic — SRE Automation Protocol
# Targets mirror the exact commands used in CI and the sandbox grading environment.
.PHONY: install test run-ui bench validate clean docker-build

install:
	pip install -r requirements.txt

test:
	python -m unittest discover tests/

# Validates the output CSV against challenge submission rules
validate:
	python validate_submission.py submission.csv

# Runs the full ranking pipeline against the 50k candidate dataset
bench:
	python rank.py --candidates data/candidates_50k.jsonl --out submission.csv

# Launches the Streamlit SRE observability dashboard
run-ui:
	streamlit run ui/app.py

# Builds the offline-ready Docker image (bakes model weights into the layer cache)
docker-build:
	docker build -t triologic-ranking-engine:latest .

clean:
	rm -rf __pycache__ .pytest_cache
	rm -f submission.csv
