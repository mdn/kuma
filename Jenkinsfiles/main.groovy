stage('Build base') {
    utils.sh_with_notify(
        'make build-base VERSION=latest',
        'Build of latest-tagged Kuma base image'
    )
}

stage('Test') {
    utils.compose_test()
}

stage('Build & push images') {
    utils.sh_with_notify(
        'make build-kuma push-kuma',
        "Build & push of commit-tagged Kuma image"
    )
    utils.sh_with_notify(
        'make push-base VERSION=latest',
        'Push of latest-tagged Kuma base image'
    )
}
