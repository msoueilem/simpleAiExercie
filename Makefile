.PHONY: install run run-pdf run-wc lint security audit check

install:
	pip install -r requirements.txt

run:
	streamlit run app.py

run-pdf:
	streamlit run pdfReviewer/pdf_reviewer.py

run-wc:
	python -m wordCount.word_analyzer $(ARGS)

lint:
	ruff check .

security:
	pip-audit -r requirements.txt

audit:
	@echo "==> Checking for hardcoded secrets..."
	@if grep -rn "sk-ant-\|sk-proj-\|AIza\|-----BEGIN" --include="*.py" .; then \
		echo "ERROR: Hardcoded secret detected."; exit 1; \
	else \
		echo "Clean."; \
	fi

check: lint security audit
	@echo "==> Validating imports..."
	@python -c "from wordCount.word_analyzer import analyze_content, analyze_file; print('wordCount OK')"
	@python -c "from pdfReviewer.core import build_prompt, parse_issues; print('pdfReviewer OK')"
	@echo "==> All checks passed."
