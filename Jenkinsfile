@Library('github.com/mozmar/jenkins-pipeline@master')

def loadBranch(String branch) {
  if (fileExists("./Jenkinsfiles/${branch}.yml")) {
    config = readYaml file: "./Jenkinsfiles/${branch}.yml"
    println "config ==> ${config}"
  }
  else {
    config = []
  }

  if (config && config.pipeline && config.pipeline.enabled == false) {
    println "Pipeline disabled."
  }
  else {
    if (config && config.pipeline && config.pipeline.script) {
      println "Loading ./Jenkinsfiles/${config.pipeline.script}.groovy"
      load "./Jenkinsfiles/${config.pipeline.script}.groovy"
    }
    else {
      println "Loading ./Jenkinsfiles/${branch}.groovy"
      load "./Jenkinsfiles/${branch}.groovy"
    }
  }
}

node {
  stage("Prepare") {
    checkout scm
    sh 'git submodule sync'
    sh 'git submodule update --init --recursive'
    setGitEnvironmentVariables()

    // When checking in a file exists in another directory start with './' or
    // prepare to fail.
    if (fileExists("./Jenkinsfiles/${env.BRANCH_NAME}.groovy") || fileExists("./Jenkinsfiles/${env.BRANCH_NAME}.yml")) {
      loadBranch(env.BRANCH_NAME)
    }
    else {
      loadBranch("default")
    }
  }
}
