stage('Test') {
    utils.compose_test()
}

stage('Build & push kuma_base image') {
    utils.sh_with_notify(
        'make build-base push-base',
        'Build and push of commit-tagged Kuma base image'
    )
}

stage('Build & push kuma image') {
    utils.sh_with_notify(
        'make build-kuma push-kuma',
        "Build & push of commit-tagged Kuma image"
    )
}
