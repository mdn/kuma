stage('Build base') {
  sh 'make build-base VERSION=latest'
}

stage('compose-test') {
  sh 'make compose-test TEST=noext' // "smoke" tests with no external deps
  sh 'make compose-test TEST="noext make build-static"' // required for many tests
  sh 'docker-compose build'
  sh 'make compose-test'
}

stage('Build & push images') {
  sh 'make build-kuma push-kuma'
  sh 'make push-base VERSION=latest'
}
