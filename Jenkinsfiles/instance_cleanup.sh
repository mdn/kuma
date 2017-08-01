#!/bin/bash
set -e

TARGET_CTX="portland.moz.works"
KEEP_ANNOTATION="mozilla.org/keep-instance"

#-----------------------------------------------------------------------
# Cheat sheet for working with keep-instance annotation:
#
# add annotation to namespace:
#  kubectl annotate namespace mdn-demo-example mozilla.org/keep-instance=1
#
# check keep-instance annotation:
#  kubectl get namespace mdn-demo-example -o json | \
#    jq -e -r '.metadata.annotations | select("mozilla.org/keep-instance") | ."mozilla.org/keep-instance"'
#
# delete annotation:
#  kubectl annotate namespace mdn-demo-example mozilla.org/keep-instance-
#-----------------------------------------------------------------------

# make sure we have kubectl installed
# make sure we're talking to the TARGET_CTX k8s context
check_k8s() {
    # make sure we have kubectl available on the CLI
    if ! which kubectl > /dev/null; then
        echo "Can't find kubectl, exiting"
        exit 1
    fi

    CURRENT_CTX=$(kubectl config current-context)

    if [ ! "${CURRENT_CTX}" = "${TARGET_CTX}" ]; then
        echo "Please set KUBECONFIG to point at the portland.moz.works cluster"
        exit 1
    fi
}

delete_ns() {
    NS=$1
    kubectl delete namespace "${NS}"
}

keep_ns() {
    NS=$1
    kubectl annotate namespace "${NS}" "${KEEP_ANNOTATION}=1"
}

delete_prompt() {
    NS=$1
    read -rp "  $NS: delete, ignore, or keep [dik]:" answer
    case ${answer:0:1} in
        d|D )
            delete_ns "$NS"
            ;;
        i|I )
            echo "  Ignoring $NS"
            ;;
        k|K )
            keep_ns "$NS"
            ;;
        * )
            echo "Invalid entry"
            ;;
    esac
}

fetch_branches() {
    echo "Fetching branches..."
    git fetch origin
}

get_demo_instances() {
    DEMO_INSTANCES=$(kubectl get namespaces -o json | jq -r '.items[].metadata.name' | grep "mdn-demo-")
    # turn it into an array
    DEMO_INSTANCES=($DEMO_INSTANCES)
}

check_k8s
fetch_branches
get_demo_instances

for instance in "${DEMO_INSTANCES[@]}"
do
    echo ""
    echo "Processing k8s namespace ${instance}"
    instance_keep=$(kubectl get namespace "${instance}" -o json | \
        jq -r ".metadata.annotations | select(\"${KEEP_ANNOTATION}\") | .\"${KEEP_ANNOTATION}\"")
    if [ "${instance_keep}" = "1" ]; then
        echo "  Instance marked as \"keep\", skipping"
        echo "  To clear keep annotation:"
        echo "    kubectl annotate namespace ${instance} ${KEEP_ANNOTATION}-"
    else
        BRANCH_NAME=$(sed "s/mdn-demo-//" <<< "$instance")
        echo "  Looking for branch \"${BRANCH_NAME}\""
        IN_GIT=$(git branch -a | grep -c "remotes/origin/${BRANCH_NAME}" | awk '{ print $1 }')
        if [ "$IN_GIT" -eq 1 ]; then
            echo "  Branch still exists"
        else
            echo "  Branch does not exist"
            delete_prompt "$instance"
        fi
    fi
done


