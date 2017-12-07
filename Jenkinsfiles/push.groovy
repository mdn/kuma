stage("Announce") {
    utils.announce_push()
}

stage("Check Pull") {
    // Check that the image can be successfully pulled from the registry.
    utils.ensure_pull()
}

stage("Prepare Infra") {
    // Checkout the "mozmeao/infra" repo's "master" branch into the
    // "infra" sub-directory of the current working directory.
    utils.checkout_repo('https://github.com/mozmeao/infra', 'master', 'infra')
}

stage('Push') {
    dir('infra/apps/mdn/mdn-aws/k8s') {
        // Run the database migrations.
        utils.migrate_db()
        // Start a rolling update of the Kuma-based deployments.
        utils.rollout()
        // Monitor the rollout until it has completed.
        utils.monitor_rollout()
    }
}
