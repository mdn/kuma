/*
 * Define utility functions.
 */

PROD_BRANCH_NAME = 'prod-push'
STAGE_BRANCH_NAME = 'stage-push'
STANDBY_BRANCH_NAME = 'standby-push'
KUMA_PIPELINE = 'kuma'

def get_commit_tag() {
    return env.GIT_COMMIT.take(7)
}

def get_target_name(target_name='') {
    if (target_name) {
        return target_name
    }
    if (env.BRANCH_NAME == PROD_BRANCH_NAME) {
        return 'prod'
    }
    if (env.BRANCH_NAME == STAGE_BRANCH_NAME) {
        return 'stage'
    }
    if (env.BRANCH_NAME == STANDBY_BRANCH_NAME) {
        return 'standby'
    }
    throw new Exception(
        'Unable to determine the target name from the branch name.'
    )
}

def get_target_script(target_file='') {
    if (target_file != null && !target_file.trim().isEmpty()) {
        return target_file
    }
    if (env.BRANCH_NAME == PROD_BRANCH_NAME) {
        return 'prod'
    }
    if (env.BRANCH_NAME == STAGE_BRANCH_NAME) {
        return 'stage'
    }
    if (env.BRANCH_NAME == STANDBY_BRANCH_NAME) {
        return 'prod.mm'
    }
    throw new Exception(
        'Unable to determine the target script from the branch name.'
    )
}

def get_region() {
    if (env.BRANCH_NAME == PROD_BRANCH_NAME) {
        return 'oregon'
    }
    if (env.BRANCH_NAME == STAGE_BRANCH_NAME) {
        return 'oregon'
    }
    if (env.BRANCH_NAME == STANDBY_BRANCH_NAME) {
        return 'germany'
    }
    throw new Exception(
        'Unable to determine the region from the branch name.'
    )
}

def get_repo_name() {
    if (env.JOB_NAME.startsWith(KUMA_PIPELINE + '/')) {
        return 'kuma'
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

def notify_slack(Map args, credential_id='slack-hook') {
    def command = "${env.WORKSPACE}/scripts/slack-notify.sh"
    withCredentials([string(credentialsId: credential_id, variable: 'HOOK')]) {
        for (arg in args) {
            command += " --${arg.key} '${arg.value}'"
        }
        command += " --hook '${HOOK}'"
        sh command
    }
}

def sh_with_notify(cmd, display, notify_on_success=false) {
    def nick = "mdn-${env.BRANCH_NAME}"
    try {
        sh cmd
        if (notify_on_success) {
            notify_slack([
                stage: display,
                status: 'success'
            ])
        }
    } catch(err) {
        notify_slack([
            stage: display,
            status: 'failure'
        ])
        throw err
    }
}

def get_revision_hash(target_file='') {
    def region = get_region()
    def target = get_target_script(target_file)
    def repo_name = get_repo_name()
    return sh(
        returnStdout: true,
        script: """
            . regions/${region}/${target}.sh >/dev/null
            make k8s-get-${repo_name}-revision-hash
        """
    ).trim()
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

def make(cmd, display, notify_on_success=false, target_file='') {
    def target = get_target_script(target_file)
    def region = get_region()
    def tag = get_commit_tag()
    def repo_upper = get_repo_name().toUpperCase()
    def cmds = """
        . regions/${region}/${target}.sh
        make ${cmd} ${repo_upper}_IMAGE_TAG=${tag}
    """
    sh_with_notify(cmds, display, notify_on_success)
}

def is_read_only_db(target_file='') {
    def region = get_region()
    def target = get_target_script(target_file)
    try {
        sh """
            . regions/${region}/${target}.sh
            echo \$KUMA_MAINTENANCE_MODE | grep -iq '^true\$'
        """
        return true
    } catch(err) {
        return false
    }
}

def migrate_db(target_file='') {
    /*
     * Migrate the database (only for kuma and writeable databases).
     */
    if ((get_repo_name() == 'kuma') && !is_read_only_db(target_file)) {
        make('k8s-db-migration-job', 'Migrate Database', false, target_file)
    }
}

def rollout(target_file='') {
    /*
     * Start a rolling update.
     */
    def repo = get_repo_name()
    make("k8s-${repo}-deployments", 'Start Rollout', false, target_file)
}

def monitor_rollout(target_file='') {
    /*
     * Monitor the rolling update until it succeeds or fails.
     */
    def repo = get_repo_name()
    make("k8s-${repo}-rollout-status", 'Check Rollout Status', true, target_file)
}

def record_rollout(target_file='') {
    /*
     * Record the rollout in external services like New Relic and SpeedCurve.
     */
    def repo = get_repo_name()
    make("k8s-${repo}-record-deployment-job", 'Record Rollout', true, target_file)
}

def announce_push(target_name='') {
    /*
     * Announce the push.
     */
    def target = get_target_name(target_name)
    def repo = get_repo_name()
    def tag = get_commit_tag()
    notify_slack([
        status: "Pushing to ${target}",
        message: "${repo} image ${tag}"
    ])
}

def compose_test() {
    def dc = 'docker-compose'
    def dc_exec = "${dc} exec -T web"
    def dc_down = "${dc} down --volumes --remove-orphans"
    def mysql_url = 'mysql://root:kuma@mysql:3306/developer_mozilla_org'
    def junit_results = '--junit-xml=/app/test_results/django.xml'
    sh_with_notify("${dc} --version", 'Check the version')
    sh_with_notify(dc_down, 'Pre-test tear-down')
    sh_with_notify("${dc} up -d", 'Start the services detached')
    sh_with_notify("${dc_exec} urlwait ${mysql_url} 30", 'Wait for MySQL')
    sh_with_notify("${dc_exec} make clean", 'Start with fresh directories')
    sh_with_notify("${dc_exec} make localecompile", 'Compile locales')
    sh_with_notify("${dc_exec} ./manage.py migrate", 'Run migrations')
    sh_with_notify("${dc_exec} pytest ${junit_results} kuma", 'Run tests')
    sh_with_notify(
        "${dc_exec} ./manage.py makemigrations --check --dry-run",
        'Ensure that no DB migrations were forgotten'
    )
    sh_with_notify(dc_down, 'Post-test tear-down')
}

return this;
