BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
MESSAGE ?= "default"
TODAY := $(shell date +'%d-%m-%Y')

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

save:
	git add .
	git commit -m "$(MESSAGE)"
	git push origin $(BRANCH)

switch-wiq-1128:
	git add .
	git stash push -m $(BRANCH)
	git checkout wiq-1128

switch-wiq-1090:
	git add .
	git stash push -m $(BRANCH)
	git checkout wiq-1090

pop:
	git stash pop stash@{$(BRANCH)}