# Variables

MESSAGE ?= "default"
TODAY := $(shell date +'%d-%m-%Y')
YESTERDAY := $(shell date -v-1d +'%d-%m-%Y')
TOMORROW := $(shell date -v+1d +'%d-%m-%Y')
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

# Daily
me:
	@code makefile
	@echo "================================="
	@echo "message: $(MESSAGE)"
	@echo "branch: $(BRANCH)"
	@echo "today: $(TODAY)"
	@echo "================================="

# The SQL command will ask for a name and create a .sql file with the snake case of the name
# Example: "Create User Table" will create create_user_table.sql 
# Additionally the command will save the file inside the sql folder and inside the TODAY subfolder
.PHONY: sql
sql:
	@read -p "Enter the name of the SQL file: " name; \
	snake=$$(echo $$name | sed -E 's/ /_/g' | tr '[:upper:]' '[:lower:]'); \
	if [ ! -d sql/$(TODAY) ]; then \
		mkdir -p sql/$(TODAY); \
	fi; \
	touch sql/$(TODAY)/$$snake.sql; \
	code sql/$(TODAY)/$$snake.sql



.PHONY: diet
diet:
	if [ ! -f diet/$(TODAY).md ]; then \
		if [ -f diet/$(YESTERDAY).md ]; then \
			cp diet/$(YESTERDAY).md diet/$(TODAY).md; \
		else \
			cp diet/diet.md diet/$(TODAY).md; \
		fi \
	fi
	code diet/$(TODAY).md

.PHONY: todo
todo:
	if [ ! -f todo/$(TODAY).md ]; then \
		if [ -f todo/$(YESTERDAY).md ]; then \
			cp todo/$(YESTERDAY).md todo/$(TODAY).md; \
		else \
			cp todo/todo.md todo/$(TODAY).md; \
		fi \
	fi
	code todo/$(TODAY).md

today:
	code journal/$(TODAY).md

yesterday:
	code journal/$(YESTERDAY).md

tomorrow:
	code journal/$(TOMORROW).md

task:
	code $(BRANCH)/$(BRANCH).md

script:
	code $(BRANCH)/__init__.py
	python $(BRANCH)/__init__.py

# Git

see:
	@echo "================================="
	git status
	@echo "================================="
	git stash list
	@echo "================================="

save:
	git add .
	git commit -m "$(MESSAGE)"
	git push origin $(BRANCH)

commit:
	git add .
	git commit -m "$(MESSAGE)"

push:
	git push origin $(BRANCH)

stash:
	git add .
	git stash push -m $(BRANCH)

pop:
	git stash list | grep "On $(BRANCH)" | head -n 1 | awk -F: '{print $$1}' | xargs -I {} git stash pop {}


# Work


switch-main:
	git add .
	git stash push -m $(BRANCH)
	git checkout main

switch-wiq-1128:
	git add .
	git stash push -m $(BRANCH)
	git checkout wiq-1128

switch-wiq-1090:
	git add .
	git stash push -m $(BRANCH)
	git checkout wiq-1090

