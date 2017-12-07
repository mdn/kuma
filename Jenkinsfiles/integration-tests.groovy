stage('Build') {
  if (!dockerImageExists("kuma-integration-tests:${GIT_COMMIT_SHORT}")) {
    dockerImageBuild("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                     ["pull": true,
                      "dockerfile": config.job.dockerfile])
  }
}

def functional_test(browser, hub_name, base_dir) {
  // Define a parallel build that runs Selenium Node for the given browser
  return {
    node {
      // Setup the pytest command
      // Timeout after 4 minutes, due to stalled nodes
      def cmd = "timeout --preserve-status 4m" +
                " py.test tests/functional" +
                " --driver Remote" +
                " --capability browserName ${browser}" +
                " --host hub" +
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
      def node_name = "kuma-selenium-node-${browser}-${BUILD_TAG}"
      def copies = 1
      if (config.job.selenium_nodes) {
        copies = config.job.selenium_nodes
        cmd += " -n ${copies}"
      }
      def test_name = "kuma-functional-tests-${browser}-${BUILD_TAG}"

      try {
        // Create named nodes
        for (int i=1; i <= copies; i++) {
          node_name_i = "${node_name}-${i}"
          dockerRun("selenium/node-${browser}:${config.job.selenium}",
                    ["docker_args": "-d" +
                                    " --name ${node_name_i}" +
                                    " --link ${hub_name}:hub"])
        }

        try {
            // Timeout after 5 minutes, if in-container timeout fails
            timeout(time: 5, unit: 'MINUTES') {
                // Run test node
                dockerRun("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                          ["docker_args": "--link ${hub_name}:hub" +
                                          " --name ${test_name}" +
                                          " --volume ${base_dir}/test_results:/test_results" +
                                          " --user 1000",
                           "cmd": cmd])
            }
        } finally {
            dockerStop(test_name)
        }
      } finally {
        for (int i=1; i <= copies; i++) {
          dockerStop("${node_name}-${i}")
        }
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
                                  " --user 1000",
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
    def hub_name = "kuma-selenium-hub-${BUILD_TAG}"
    allTests['chrome'] = functional_test('chrome', hub_name, base_dir)
    allTests['firefox'] = functional_test('firefox', hub_name, base_dir)
    allTests['headless'] = headless_test(base_dir)

    def nick =  "ci-bot"
    try {
        // Setup the selenium hub
        dockerRun("selenium/hub:${config.job.selenium}",
                  ["docker_args": "-d --name ${hub_name}"])

        try {
            // Run the tests in parallel
            parallel allTests
            // Notify on success
            utils.notify_irc([
                irc_nick: nick,
                stage: 'Test',
                status: 'success'
            ])
        } catch(err) {
            utils.notify_irc([
                irc_nick: nick,
                stage: 'Test',
                status: 'failure'
            ])
            throw err
        } finally {
            dockerStop(hub_name)
        }
    } finally {
        dockerStop(hub_name)
    }
}

