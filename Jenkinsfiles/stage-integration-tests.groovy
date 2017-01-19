stage('Build') {
  if (!dockerImageExists("kuma-integration-tests:${GIT_COMMIT_SHORT}")) {
    dockerImageBuild("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                     ["pull": true,
                      "dockerfile": config.job.dockerfile])
  }
}

stage('Tests') {
  dockerRun("selenium/hub:${config.job.selenium}", ["docker_args": "--name selenium-hub-${BUILD_TAG}"]) {
    dockerRun("selenium/node-firefox:${config.job.selenium}", ["docker_args": "--link selenium-hub-${BUILD_TAG}:hub", "copies": config.job.selenium_nodes]) {
      dockerRun("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                ["docker_args": "--link selenium-hub-${BUILD_TAG}:hub",
                 "cmd": "py.test tests/functional --driver Remote --capability browserName firefox --host hub --base-url='${config.job.base_url}'"])
    }
  }
}
