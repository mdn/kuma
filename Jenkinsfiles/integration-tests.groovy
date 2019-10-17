test_image = "kuma-integration-tests:${GIT_COMMIT_SHORT}"

stage('Build') {
    try {
        sh "docker image inspect ${test_image}"
    } catch(err) {
        sh "docker build -f ${config.job.dockerfile} -t ${test_image} ."
    }
}

def headless_tests(base_dir) {
    // Setup the pytest command (timeout at 8 min for stalled nodes).
    def cmd = "timeout --preserve-status 8m" +
              " pytest tests/headless" +
              " --base-url='${config.job.base_url}'" +
              " --junit-xml=/app/test_results/headless.xml" +
              " --reruns=2"
    def run = "docker run --name headless-${BUILD_TAG}"
    sh "${run} --rm --volume ${base_dir}:/app:z ${test_image} ${cmd}"
}

stage('Test') {
    def base_dir = pwd()
    def nick =  "ci-bot"
    try {
        headless_tests(base_dir)
        utils.notify_slack([stage: 'Test', status: 'success'])
    } catch(err) {
        utils.notify_slack([stage: 'Test', status: 'failure'])
        throw err
    }
}
