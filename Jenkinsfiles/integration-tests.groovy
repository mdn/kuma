stage('Build') {
  if (!dockerImageExists("kuma-integration-tests:${GIT_COMMIT_SHORT}")) {
    dockerImageBuild("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                     ["pull": true,
                      "dockerfile": config.job.dockerfile])
  }
}

stage('Functional') {
  def cmd = "py.test tests/functional" +
            " --driver Remote" +
            " --capability browserName firefox" +
            " --host hub" +
            " --base-url='${config.job.base_url}'"
  if (config.job && config.job.tests) {
    cmd += " -m \"${config.job.tests}\""
  }
  if (config.job && config.job.maintenance_mode) {
    cmd += " --maintenance-mode"
  }

  dockerRun("selenium/hub:${config.job.selenium}",
            ["docker_args": "--name selenium-hub-${BUILD_TAG}"]) {
    dockerRun("selenium/node-firefox:${config.job.selenium}",
              ["docker_args": "--link selenium-hub-${BUILD_TAG}:hub",
               "copies": config.job.selenium_nodes]) {
      dockerRun("kuma-integration-tests:${GIT_COMMIT_SHORT}",
                ["docker_args": "--link selenium-hub-${BUILD_TAG}:hub",
                 "cmd": cmd])
    }
  }
}

stage('Headless') {
  dockerRun("kuma-integration-tests:${GIT_COMMIT_SHORT}",
            ["docker_args": "--volume ${pwd}/test_results:/test_results"
             "cmd": "py.test tests/headless" +
                    " --base-url='${config.job.base_url}'"])
}
