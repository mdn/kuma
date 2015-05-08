VENDOR_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

packages:
	@echo Installing packages into vendor dir $(VENDOR_DIR)
	pip install -t "$(VENDOR_DIR)/packages" -r $(VENDOR_DIR)/../requirements/packages.txt

.PHONY: packages
