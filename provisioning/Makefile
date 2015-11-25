PROVISIONING_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

roles:
	@echo Updating Ansible roles into roles dir $(PROVISIONING_DIR)
	ansible-galaxy install -p "$(PROVISIONING_DIR)/roles" -r "$(PROVISIONING_DIR)/roles.txt" -f

.PHONY: roles
