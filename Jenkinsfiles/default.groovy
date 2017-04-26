stage('compose-test') {
  sh 'make compose-test TEST=noext' // "smoke" tests with no external deps
  sh 'make compose-test TEST="noext make build-static"' // required for many tests
  sh 'docker-compose build'
  sh 'make compose-test'
}

stage('Build & push kuma_base image') {
  sh 'make build-base push-base'
}

stage('Build & push kuma image') {
  sh 'make build-kuma push-kuma'
}
