#!/bin/bash

set -x

# DEIS_APP contains the mdn-demo- branch prefix
KUBE_NAMESPACE="${DEIS_APP}"

# relatively static vars
MYSQL_PORT=3306
MDN_SAMPLE_DB_URL=https://mdn-downloads.s3-us-west-2.amazonaws.com/mdn_sample_db.sql.gz
MYSQL_DATABASE=developer_mozilla_org
DOCKER_IMAGE="quay.io/mozmar/mdn-myql-demo-import-helper:latest"
POD_NAME="mdn-db-import"

cleanup_old_pods() {
    echo -n "Clearing out old pods..."
    kubectl -n "${KUBE_NAMESPACE}" delete pod "${POD_NAME}" > /dev/null 2>&1 || true
    echo "Finished"
}

fetch_pod_ip() {
    echo "Fetching MySQL pod IP"
    MYSQL_IP=$(kubectl get service mysql -n "${KUBE_NAMESPACE}" -o json | jq -r '.spec.clusterIP')
    echo "MySQL IP = ${MYSQL_IP}"
}

run_db_import() {
    echo "Starting db import pod ${POD_NAME} in namespace ${KUBE_NAMESPACE}"
    kubectl run mdn-db-import \
        --image ${DOCKER_IMAGE} \
        -n "${KUBE_NAMESPACE}" \
        --restart=Never \
        --env="MYSQL_ROOT_PASSWORD=kuma" \
        --env="MYSQL_USER=root" \
        --env="MYSQL_PASSWORD=kuma" \
        --env="MYSQL_DATABASE=$MYSQL_DATABASE" \
        --env="MYSQL_IP=$MYSQL_IP" \
        --env="MYSQL_PORT=$MYSQL_PORT" \
        --env="MDN_SAMPLE_DB_URL=$MDN_SAMPLE_DB_URL"
    echo "DB import pod started"
}

cleanup_old_pods
fetch_pod_ip
run_db_import
echo "DB import script complete"
