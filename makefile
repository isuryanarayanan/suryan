MESSAGE ?= "Default update message"
PROJECT ?= "wareiq-app/wq-1090"


me:
	code makefile

task:
	code wareiq-app/wq-1090/tasks.md

save:
	git add .
	git commit -m "$(MESSAGE)"
	git push origin $(PROJECT)

1128:
	git stash push -m $(PROJECT)
	git checkout wareiq-app/wq-1128
	git stash pop stash^{/wareiq-app/wq-1128}
