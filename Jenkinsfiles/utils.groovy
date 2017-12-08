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

def sh_with_notify(cmd, display, notify_on_success=false) {
    def nick = "mdn-${env.BRANCH_NAME}"
    try {
        sh cmd
        if (notify_on_success) {
            notify_irc([
                irc_nick: nick,
                stage: display,
                status: 'success'
            ])
        }
    } catch(err) {
        notify_irc([
            irc_nick: nick,
            stage: display,
            status: 'failure'
        ])
        throw err
    }
}

def ensure_pull() {
    /*
     * This can be used to avoid deploying images to Kubernetes that don't
     * exist in the registry, since the deployment to Kubernetes will succeed
     * (the deployment just cares that an image URL is provided, not that
     * it actually exists) but each pod's image download will then fail
     * causing the pod to loop in an image-pull error.
     */
    def repo = get_repo_name()
    def tag = get_commit_tag()
    sh_with_notify(
        "make pull-${repo}",
        "Ensure pull of ${repo} image ${tag} works"
    )
}

def make(cmd, display) {
    def target = get_target()
    def tag = get_commit_tag()
    def repo_upper = get_repo_name().toUpperCase()
    def cmds = """
        . regions/portland/${target}.sh
        make ${cmd} ${repo_upper}_IMAGE_TAG=${tag}
    """
    sh_with_notify(cmds, display, true)
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
        irc_nick: "mdn-${env.BRANCH_NAME}",
        status: "Pushing to ${target}",
        message: "${repo} image ${tag}"
    ])
}

def compose_test() {
    def dc = 'docker-compose -f docker-compose.yml -f docker-compose.test.yml'
    // Pre-test tear down to ensure we're starting with a clean slate.
    sh_with_notify("${dc} down", 'Pre-test tear-down')
    // Run the "smoke" tests with no external dependencies.
    sh_with_notify("${dc} run noext", 'Smoke tests')
    // Build the static assets required for many tests.
    sh_with_notify("${dc} run noext make build-static", 'Build static assets')
    // Run the Kuma tests, building the mysql image before starting.
    sh_with_notify("${dc} up --build --exit-code-from=test test", 'Kuma tests')
    // Tear everything down.
    sh_with_notify("${dc} down", 'Post-test tear-down')
}

return this;
