VENDOR_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

packages:
	@echo Purging vendor dir $(VENDOR_DIR)
	rm -rf $(VENDOR_DIR)/packages/*
	rm -rf $(VENDOR_DIR)/packages
	@echo Installing packages into vendor dir $(VENDOR_DIR)
	pip install -U -t "$(VENDOR_DIR)/packages" -r $(VENDOR_DIR)/../requirements/packages.txt

.PHONY: packages
