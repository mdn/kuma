/*
 * Define utility functions.
 */

def checkout_github(repo, branch, relative_target_dir) {
    checkout(
        [$class: 'GitSCM',
         userRemoteConfigs: [[url: "https://github.com/${repo}"]],
         branches: [[name: "refs/heads/${branch}"]],
         extensions: [[$class: 'RelativeTargetDirectory',
                       relativeTargetDir: relative_target_dir]],
         doGenerateSubmoduleConfigurations: false,
         submoduleCfg: []]
    )
}

def notify_irc(Map args) {
    def command = "${env.WORKSPACE}/scripts/irc-notify.sh"
    for (arg in args) {
        command += " --${arg.key} '${arg.value}'"
    }
    sh command
}

def make(setup, cmd) {
    sh """
        . ${setup}
        make ${cmd} KUMA_IMAGE_TAG=${env.GIT_COMMIT_SHORT}
    """
}

def make_stage(cmd, cmd_display) {
    try {
        make('regions/portland/stage.sh', cmd)
        notify_irc([
            irc_nick: 'mdnstagepush',
            stage: cmd_display,
            status: 'success'
        ])
    } catch(err) {
        notify_irc([
            irc_nick: 'mdnstagepush',
            stage: cmd_display,
            status: 'failure'
        ])
        throw err
    }
}

def migrate_stage_db() {
    make_stage('k8s-db-migration-job', 'Migrate Database')
}

def rollout_to_stage() {
    make_stage('k8s-kuma-deployments', 'Start Rollout')
}

def monitor_rollout_to_stage() {
    make_stage('k8s-kuma-rollout-status', 'Check Rollout Status')
}

return this;
