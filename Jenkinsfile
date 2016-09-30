node {
    stage 'git'
    checkout scm

    env.DEIS_BIN = 'deis2'
    env.DEIS_PROFILE = 'dev-usw'

    switch (env.BRANCH_NAME) {
      case 'master':
        env.DEIS_APP = 'mdn-dev'

        stage 'Build base'
        echo 'make build-base VERSION=latest'

        stage 'compose-test'
        sh 'make compose-test TEST=noext' // "smoke" tests with no external deps
        sh 'make compose-test TEST="noext make build-static"' // required for many tests
        sh 'docker-compose build'
        sh 'make compose-test'

        stage 'Build & push kuma image'
        sh 'make build-kuma push-kuma'

        stage "Deploy pull"
        sh "make deis-pull"

        stage "DB migrations"
        sh "make k8s-migrate"
        break

      default:
        env.DEIS_APP = 'mdn-' + env.BRANCH_NAME

        stage 'Build & push kuma image'
        sh 'make build-kuma push-kuma'
        // this assumes the latest base image from master is compatible with this branch
        // TODO: example special case branch that builds and uses a different base image

        stage "create & config deis app"
        sh "make deis-create"

        stage "k8s backing services"
        sh "kubectl --namespace=${env.DEIS_APP} apply -f k8s/"

        stage "deis pull"
        sh "make deis-pull"

        stage "DB migrations"
        sh "make k8s-migrate"

        stage "scale worker"
        sh "make deis-scale-worker"

        break
    }
}
