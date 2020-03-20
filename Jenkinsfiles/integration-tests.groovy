stage('Build base') {
    utils.sh_with_notify(
        'make build-base VERSION=latest',
        'Build of latest-tagged Kuma base image'
    )
}

stage('Test') {
    try {
        // Setup the pytest command (timeout at 8 min for stalled nodes).
        def cmd = "timeout --preserve-status 8m" +
                  " pytest tests" +
                  " --base-url='${config.job.base_url}'" +
                  " --junit-xml=/app/test_results/integration.xml" +
                  " --reruns=2"
        def run = "docker run --user ${env['UID']} --name headless-${BUILD_TAG}"
        sh "${run} --rm --volume ${pwd()}:/app:z mdnwebdocs/kuma_base ${cmd}"
        utils.notify_slack([stage: 'Test', status: 'success'])
    } catch(err) {
        utils.notify_slack([stage: 'Test', status: 'failure'])
        throw err
    }
}
