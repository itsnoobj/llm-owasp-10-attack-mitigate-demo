.PHONY: setup demo01 demo02 demo03 demo04 demo05 demo06 demo07 demo08 demo09 demo10 demo03-live slides

setup:
	python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

demo01:
	python3 LLM01-prompt-injection/web.py

demo02:
	python3 LLM02-sensitive-info-disclosure/web.py

demo03:
	python3 LLM03-supply-chain/demo.py

demo03-live:
	@echo "Run in two terminals:"
	@echo "  Terminal 1: python3 LLM03-supply-chain/live-exfil/c2_server.py"
	@echo "  Terminal 2: python3 LLM03-supply-chain/live-exfil/malicious_tool.py"

demo04:
	python3 LLM04-data-poisoning/demo.py

demo05:
	python3 LLM05-improper-output-handling/demo.py

demo06:
	python3 LLM06-excessive-agency/web.py

demo07:
	python3 LLM07-system-prompt-leakage/web.py

demo08:
	python3 LLM08-vector-embedding-weaknesses/web.py

demo09:
	python3 LLM09-misinformation/web.py

demo10:
	python3 LLM10-unbounded-consumption/demo.py

slides:
	presenterm slides.md
