
dev:
	fastapi dev .\src\main.py

test:
	pytest

format:
	ruff format

stress:
	locust -f .\test\stress.py --headless -u 100 -r 10 -t 20s -H http://127.0.0.1:8000 --html .\reports\stress_test.html
