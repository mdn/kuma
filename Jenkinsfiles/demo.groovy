stage('Build & push images') {
  sh 'make build-kuma push-kuma'
}

stage('Deploy') {
  env.KUBECONFIG = "${env.HOME}/.kube/virginia.kubeconfig"
  env.DEIS_PROFILE = 'virginia'
  env.DEIS_BIN = 'deis2'
  env.DEIS_APP = 'mdn-' + env.BRANCH_NAME

  sh 'make deis-create-and-or-config'
  sh "KUBECONFIG=${env.KUBECONFIG} kubectl --namespace=${env.DEIS_APP} apply -f k8s/"
  sh 'make deis-pull'
  sh 'make deis-migrate'
  sh 'make deis-scale-worker'
}
