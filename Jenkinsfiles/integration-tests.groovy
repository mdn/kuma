test_image = "kuma-integration-tests:${GIT_COMMIT_SHORT}"

stage('Build') {
    try {
        sh "docker image inspect ${test_image}"
    } catch(err) {
        sh "docker build -f ${config.job.dockerfile} -t ${test_image} ."
    }
}

def functional_test(browser, base_dir) {
    // Define a parallel build that runs stand-alone Selenium
    // for the given browser.
    return {
        node {
            // Setup the extra arguments for the pytest command.
            def pytest_opts = ""
            if (config.job && config.job.tests) {
                pytest_opts += "-m '${config.job.tests}'"
            }
            if (config.job && config.job.maintenance_mode) {
                pytest_opts += " --maintenance-mode"
            }
            // Timeout at 7 minutes for stalled nodes.
            withEnv(["TIMEOUT=7m",
                     "BROWSER=${browser}",
                     "PYTEST_OPTS=${pytest_opts}",
                     "BASE_URL=${config.job.base_url}",
                     "TEST_IMAGE_TAG=${GIT_COMMIT_SHORT}",
                     "SELENIUM_IMAGE_TAG=${config.job.selenium}",
                     "COMPOSE_PROJECT_NAME=${browser}-${BUILD_TAG}",
                     "COMPOSE_FILE=${base_dir}/docker-compose.selenium.yml"])
            {
                sh 'docker-compose pull selenium'
                sh 'docker-compose up -d selenium'
                try {
                    sh 'docker-compose run tests'
                } finally {
                    sh 'docker-compose down --volumes --remove-orphans'
                }
            }
        }
    }
}

def headless_test(base_dir) {
    return {
        node {
            // Setup the pytest command (timeout at 8 min for stalled nodes).
            def cmd = "timeout --preserve-status 8m" +
                      " py.test tests/headless" +
                      " --base-url='${config.job.base_url}'" +
                      " --junit-xml=/app/test_results/headless.xml" +
                      " --reruns=2"
            def run = "docker run --name headless-${BUILD_TAG}"
            sh "${run} --rm --volume ${base_dir}:/app:z ${test_image} ${cmd}"
        }
    }
}

stage('Test') {
    // Setup parallel tests
    def allTests = [:]
    def base_dir = pwd()
    allTests['chrome'] = functional_test('chrome', base_dir)
    allTests['firefox'] = functional_test('firefox', base_dir)
    allTests['headless'] = headless_test(base_dir)

    def nick =  "ci-bot"

    try {
        // Run the tests in parallel
        parallel allTests
        // Notify on success
        utils.notify_irc([irc_nick: nick, stage: 'Test', status: 'success'])
        utils.notify_slack([stage: 'Test', status: 'success'])
    } catch(err) {
        utils.notify_irc([irc_nick: nick, stage: 'Test', status: 'failure'])
        utils.notify_slack([stage: 'Test', status: 'failure'])
        throw err
    }
}
