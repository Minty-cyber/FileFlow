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

GREEN  := \033[0;32m
BLUE := \033[0;34m
PURPLE := \033[0;35m
PINK := \033[1;35m
YELLOW := \033[1;33m
RED    := \033[0;31m
RESET  := \033[0m


help:
	@printf "${YELLOW}Available commands:${RESET}\n"
	@printf "  ${GREEN}install${RESET}         - Install project dependencies\n"
	@printf "  ${GREEN}run${RESET}             - Run development server\n"
	@printf "  ${GREEN}test${RESET}            - Run tests\n"
	@printf "  ${GREEN}lint${RESET}            - Run code linting\n"
	@printf "  ${GREEN}format${RESET}          - Format code\n"
	@printf "  ${GREEN}clean${RESET}           - Remove cached files\n"
	@printf "  ${GREEN}migrate${RESET}         - Apply database migrations\n"
	@printf "  ${GREEN}migrations${RESET}  - Create new database migrations\n"
	@printf "  ${GREEN}shell${RESET}           - Open Django shell\n"
	@printf "  ${GREEN}collectstatic${RESET}   - Collect static files\n"
	@printf "  ${GREEN}app${RESET}             - Create a new app (name=your_app)\n"
	@printf "  ${GREEN}command${RESET}         - Create a custom Django command (app=your_app name=your_command)\n"
	@printf "  ${GREEN}superuser${RESET}       - Create a superuser\n"

	

test:
	@printf "${YELLOW}Going Test Mode...${RESET}\n"
	docker compose --profile app_test run --rm test
start:
	@printf "${YELLOW}Starting development server...${RESET}\n"
	docker compose up
mongo:
	@printf "${BLUE}Starting MongoDB Database..${RESET}\n"
	docker exec -it mongodb mongosh -u root -p example --authenticationDatabase admin

db:
	@printf "${PURPLE}Starting Postgres Database...${RESET}\n"
	docker exec -it db bash
backend:
	@printf "${PINK}Spinning Backend Shell...${RESET}\n"
	docker exec -it backend bash
build:
	@printf "${PURPLE}Starting Build...${RESET}\n"
	docker compose up --build
down: 
	@printf "${RED}Cleaning containers...${RESET}\n"
	docker compose down


	