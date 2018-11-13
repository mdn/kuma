stage('Build') {
  if (!dockerImageExists("kuma-integration-tests:${GIT_COMMIT_SHORT}")) {
    dockerImageBuild("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                     ["pull": true,
                      "dockerfile": config.job.dockerfile])
  }
}

def functional_test(browser, base_dir) {
  // Define a parallel build that runs stand-alone Selenium for the given browser
  return {
    node {
      def port = (browser == 'chrome') ? '4444' : '4445'
      def test_name = "kuma-functional-tests-${browser}-${BUILD_TAG}"
      def selenium_name = "kuma-selenium-standalone-${browser}-${BUILD_TAG}"
      // Setup the pytest command
      // Timeout after 6 minutes, due to stalled nodes
      def cmd = "timeout --preserve-status 6m" +
                " py.test tests/functional" +
                " --driver Remote" +
                " --capability browserName ${browser}" +
                " --host ${selenium_name}" +
                " --port ${port}" +
                " --base-url='${config.job.base_url}'" +
                " --junit-prefix=${browser}" +
                " --junit-xml=/test_results/functional-${browser}.xml" +
                " --reruns=2" +
                " -vv"
      if (config.job && config.job.tests) {
        cmd += " -m \"${config.job.tests}\""
      }
      if (config.job && config.job.maintenance_mode) {
        cmd += " --maintenance-mode"
      }

      try {
        // Create the Selenium stand-alone container for the given browser
        // The "--shm-size=2g" is recommended to avoid browser crashes (see
        // https://github.com/SeleniumHQ/docker-selenium#running-the-images)
        // which we've seen in our chrome integration tests without it.
        dockerRun("selenium/standalone-${browser}:${config.job.selenium}",
                  ["docker_args": "-d " +
                                  "--shm-size=2g " +
                                  "-e SE_OPTS='-port ${port}' "  +
                                  "--name ${selenium_name}"])

        try {
            // Timeout after 7 minutes, if in-container timeout fails
            timeout(time: 7, unit: 'MINUTES') {
                // Run test node
                dockerRun("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                          ["docker_args": "--link ${selenium_name} " +
                                          "--name ${test_name} " +
                                          "--volume ${base_dir}/test_results:/test_results " +
                                          "--user ${UID}",
                           "cmd": cmd])
            }
        } finally {
            dockerStop(test_name)
        }
      } finally {
          dockerStop(selenium_name)
      }
    }
  }
}

def headless_test(base_dir) {
  // Define a parallel build that runs the "headless" (requests, no Selenium) tests
  return {
    node {
      def test_name = "kuma-test-headless-${BUILD_TAG}"
      dockerRun("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                  ["docker_args": "--volume ${base_dir}/test_results:/test_results" +
                                  " --name ${test_name}" +
                                  " --user ${UID}",
                  "cmd": "py.test tests/headless" +
                          " --base-url='${config.job.base_url}'" +
                          " --junit-xml=/test_results/headless.xml" +
                          " --reruns=2"])
    }
  }
}

stage('Test') {
    // Setup parallel tests
    def allTests = [:]
    def base_dir = pwd()
    allTests['chrome'] = functional_test('chrome', base_dir)
    allTests['firefox'] = functional_test('firefox', base_dir)
    // allTests['headless'] = headless_test(base_dir)

    def nick =  "ci-bot"

    try {
        // Run the tests in parallel
        parallel allTests
        // Notify on success
        utils.notify_irc([irc_nick: nick, stage: 'Test', status: 'success'])
    } catch(err) {
        utils.notify_irc([irc_nick: nick, stage: 'Test', status: 'failure'])
        throw err
    }
}
