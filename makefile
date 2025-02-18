# Variables

MESSAGE ?= "default"
TODAY := $(shell date +'%d-%m-%Y')
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

# Daily
me:
	@code makefile
	@echo "================================="
	@echo "message: $(MESSAGE)"
	@echo "branch: $(BRANCH)"
	@echo "today: $(TODAY)"
	@echo "================================="

today:
	code journal/$(TODAY).md

task:
	code $(BRANCH)/$(BRANCH).md

# Git

commit:
	git add .
	git commit -m "$(MESSAGE)"

push:
	git push origin $(BRANCH)

stash:
	git add .
	git stash push -m $(BRANCH)

pop:
	git stash pop $$(git stash list | grep "On $(BRANCH)" | head -n 1 | awk -F: '{print $$1}')


# Work

main:
	git checkout main

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

