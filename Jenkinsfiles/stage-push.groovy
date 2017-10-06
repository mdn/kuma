stage("Announce") {
    utils.notify_irc([
        irc_nick: 'mdnstagepush',
        status: 'Pushing to Stage',
        message: "Kuma image ${env.GIT_COMMIT_SHORT}"
    ])
}

stage("Prepare Infra") {
    // Checkout the "mozmeao/infra" repo's "master" branch into the
    // "infra" sub-directory of the current working directory.
    utils.checkout_github('mozmeao/infra', 'master', 'infra')
}

stage('Push') {
    dir('infra/apps/mdn/mdn-aws/k8s') {
        // Run the database migrations.
        utils.migrate_stage_db()
        // Perform a rolling update of the Kuma-based deployments.
        utils.rollout_to_stage()
        // Watch the rollout status until it has completed.
        utils.monitor_rollout_to_stage()
    }
}
