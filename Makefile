# @echo "Opening coverage report..."
# 	@if [ -f htmlcov/index.html ]; then \
# 		if command -v xdg-open >/dev/null 2>&1; then \
# 			xdg-open htmlcov/index.html; \
# 		elif command -v open >/dev/null 2>&1; then \
# 			open htmlcov/index.html; \
# 		elif command -v start >/dev/null 2>&1; then \
# 			start htmlcov/index.html; \
# 		else \
# 			echo "Please open htmlcov/index.html manually."; \
# 		fi \
# 	else \
# 		echo "Coverage report not found. Did coverage run generate htmlcov/index.html?"; \
# 	fi
	

test:
	docker compose --profile app_test run --rm test

db:
	docker exec -it db bash
backend:
	docker exec -it backend bash
build:
	docker compose up --build

	