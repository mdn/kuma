/*
 * Define utility functions.
 */

PROD_BRANCH_NAME = 'prod-push'
STAGE_BRANCH_NAME = 'stage-push'
KUMA_PIPELINE = 'mdn_multibranch_pipeline'
KUMASCRIPT_PIPELINE= 'kumascript_multibranch_pipeline'

def get_commit_tag() {
    return env.GIT_COMMIT.take(7)
}

def get_target() {
    if (env.BRANCH_NAME == PROD_BRANCH_NAME) {
        return 'prod'
    }
    if (env.BRANCH_NAME == STAGE_BRANCH_NAME) {
        return 'stage'
    }
    throw new Exception(
        'Unable to determine the target from the branch name.'
    )
}

def get_repo_name() {
    if (env.JOB_NAME.startsWith(KUMA_PIPELINE)) {
        return 'kuma'
    }
    if (env.JOB_NAME.startsWith(KUMASCRIPT_PIPELINE)) {
        return 'kumascript'
    }
    throw new Exception(
        'Unable to determine the repo name from the job name.'
    )
}

def checkout_repo(repo, branch, relative_target_dir) {
    checkout(
        [$class: 'GitSCM',
         userRemoteConfigs: [[url: repo]],
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

def make(cmd, cmd_display) {
    def target = get_target()
    def tag = get_commit_tag()
    def nick = "mdn${target}push"
    def repo_upper = get_repo_name().toUpperCase()
    try {
        /*
         * Run the actual make command within the proper environment.
         */
        sh """
            . regions/portland/${target}.sh
            make ${cmd} ${repo_upper}_IMAGE_TAG=${tag}
        """
        notify_irc([
            irc_nick: nick,
            stage: cmd_display,
            status: 'success'
        ])
    } catch(err) {
        notify_irc([
            irc_nick: nick,
            stage: cmd_display,
            status: 'failure'
        ])
        throw err
    }
}

def migrate_db() {
    /*
     * Migrate the database (only for kuma).
     */
    if (get_repo_name() == 'kuma') {
        make('k8s-db-migration-job', 'Migrate Database')
    }
}

def rollout() {
    /*
     * Start a rolling update.
     */
    def repo = get_repo_name()
    make("k8s-${repo}-deployments", 'Start Rollout')
}

def monitor_rollout() {
    /*
     * Monitor the rolling update until it succeeds or fails.
     */
    def repo = get_repo_name()
    make("k8s-${repo}-rollout-status", 'Check Rollout Status')
}

def announce_push() {
    /*
     * Announce the push.
     */
    def target = get_target()
    def repo = get_repo_name()
    def tag = get_commit_tag()
    notify_irc([
        irc_nick: "mdn${target}push",
        status: "Pushing to ${target}",
        message: "${repo} image ${tag}"
    ])
}

return this;
