stage('Build & push images') {
  sh 'make build-kuma push-kuma'
}

stage('Deploy') {
  env.KUBECONFIG = "${env.HOME}/.kube/portland.kubeconfig"
  env.DEIS_PROFILE = 'portland'
  env.DEIS_BIN = 'deis2'
  env.DEIS_APP = 'mdn-demo-' + env.BRANCH_NAME
  env.DJANGO_SETTINGS_MODULE = 'kuma.settings.prod'
  assert env.BRANCH_NAME.matches("[a-z0-9-]*[a-z0-9]")

  sh 'make deis-create-and-or-config'
  sh 'make render-k8s-templates'
  sh 'kubectl config use-context portland'
  sh 'kubectl apply -f k8s/ -n ' + env.DEIS_APP
  sh 'make deis-pull'
  sh 'make deis-migrate'
  sh 'make demo-db-import'
  sh 'make deis-scale-api-and-worker'
}
