REPORTER = spec
BRANCH = master

test: test-unit

test-unit:
	@NODE_ENV=test ./node_modules/.bin/mocha \
		--reporter $(REPORTER)

open-cov: test-cov
	@open lib-cov/coverage.html

test-cov: clean lib-cov
	@LIB_COV=1 $(MAKE) test-unit REPORTER=html-cov > lib-cov/coverage.html

lib-cov:
	@jscoverage lib lib-cov

clean:
	rm -fr lib-cov

push: test
	@git push origin $(BRANCH)
