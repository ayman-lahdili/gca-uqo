
format:
	ruff format

stress:
	locust -f .\src\scripts\stress_test.py --headless -u 100 -r 5 -t 20s -H http://127.0.0.1:8000 --html stress_test.html