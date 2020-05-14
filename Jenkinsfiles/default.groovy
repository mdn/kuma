stage('Build base') {
    utils.sh_with_notify(
        'make build-base VERSION=latest',
        'Build of latest-tagged Kuma base image'
    )
}

stage('Build & push images') {
    utils.sh_with_notify(
        'make build-kuma push-kuma',
        "Build & push of commit-tagged Kuma image"
    )
}
