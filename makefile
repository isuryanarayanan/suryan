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


.PHONY: diet
diet:
	if [ ! -f diet/$(TODAY).md ]; then \
		if [ -f diet/$(YESTERDAY).md ]; then \
			cp diet/$(YESTERDAY).md diet/$(TODAY).md; \
		else \
			cp diet.md diet/$(TODAY).md; \
		fi \
	fi
	code diet/$(TODAY).md

todo:
	code todo.md

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

