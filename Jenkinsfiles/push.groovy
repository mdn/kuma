stage("Announce") {
    utils.announce_push()
}

stage("Check Pull") {
    // Check that the image can be successfully pulled from the registry.
    utils.ensure_pull()
}

stage("Prepare Infra") {
    // Checkout the "mdn/infra" repo's "master" branch into the
    // "infra" sub-directory of the current working directory.
    utils.checkout_repo('https://github.com/mdn/infra', 'master', 'infra')
}

stage('Push') {
    dir('infra/apps/mdn/mdn-aws/k8s') {
        def current_revision_hash = utils.get_revision_hash()
        withEnv(["TO_REVISION_HASH=${env.GIT_COMMIT}",
                 "FROM_REVISION_HASH=${current_revision_hash}"]) {
            // Run the database migrations.
            utils.migrate_db()
            // Start a rolling update of the Kuma-based deployments.
            utils.rollout()
            // Monitor the rollout until it has completed.
            utils.monitor_rollout()
            // Record the rollout in external services like New-Relic.
            utils.record_rollout()
        }
    }
}
