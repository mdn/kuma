node {
    stage 'git'
    checkout scm

    env.DEIS_BIN = 'deis2'
    env.DEIS_PROFILE = 'dev-usw'

    switch (env.BRANCH_NAME) {
      case 'master':
        stage('Build base') {
          sh 'make build-base VERSION=latest'
        }

        stage('compose-test') {
          sh 'make compose-test TEST=noext' // "smoke" tests with no external deps
          sh 'make compose-test TEST="noext make build-static"' // required for many tests
          sh 'docker-compose build'
          sh 'make compose-test'
        }

        stage('Build & push kuma image') {
          sh 'make build-kuma push-kuma'
        }

        break

      default:
        // this assumes the latest base image from master is compatible with this branch
        // TODO: example special case branch that builds and uses a different base image
        stage('compose-test') {
          sh 'make compose-test TEST=noext' // "smoke" tests with no external deps
          sh 'make compose-test TEST="noext make build-static"' // required for many tests
          sh 'docker-compose build'
          sh 'make compose-test'
        }

        stage('Build & push kuma image') {
          sh 'make build-kuma push-kuma'
        }

        break
    }
}
