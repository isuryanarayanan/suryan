MESSAGE ?= "update"
PROJECT ?= "wareiq-app/wq-1090"



me:
	code makefile
	echo $(MESSAGE)
	echo $(PROJECT)

task:
	code wareiq-app/wq-1090/tasks.md

save:
	git add .
	git commit -m "$(MESSAGE)"
	git push origin $(PROJECT)

switch-1128:
	git add .
	git stash push -m $(PROJECT)
	git checkout wareiq-app/wq-1128
	git stash pop stash^{1128}
