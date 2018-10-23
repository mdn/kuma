#!groovy

@Library('github.com/mozmeao/jenkins-pipeline@master')

def loadBranch(String branch) {
  utils = load 'Jenkinsfiles/utils.groovy'
  if (fileExists("./Jenkinsfiles/${branch}.yml")) {
    config = readYaml file: "./Jenkinsfiles/${branch}.yml"
    println "config ==> ${config}"
  } else {
    config = []
  }

  if (config && config.pipeline && config.pipeline.enabled == false) {
    println "Pipeline disabled."
  } else {
    if (config && config.pipeline && config.pipeline.script) {
      println "Loading ./Jenkinsfiles/${config.pipeline.script}.groovy"
      load "./Jenkinsfiles/${config.pipeline.script}.groovy"
    } else {
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
    // Set UID to jenkins
    env['UID'] = sh(returnStdout: true, script: 'id -u jenkins').trim()
    // Prepare for junit test results
    sh "mkdir -p test_results"
    sh "rm -f test_results/*.xml"

    // When checking in a file exists in another directory start with './' or
    // prepare to fail.
    try {
      if (fileExists("./Jenkinsfiles/${env.BRANCH_NAME}.groovy") || fileExists("./Jenkinsfiles/${env.BRANCH_NAME}.yml")) {
        loadBranch(env.BRANCH_NAME)
      } else {
        loadBranch("default")
      }
    }
    finally {
      if (findFiles(glob: 'test_results/*.xml')) {
        junit 'test_results/*.xml'
      }
    }
  }
}
