export APP=mdn-demo-$(git rev-parse --abbrev-ref HEAD)
eval "cat <<EOF
apiVersion: v1
kind: Service
metadata:
  labels:
    app: ${APP}
  name: api
  namespace: ${APP}
spec:
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 8000
  selector:
    app: ${APP}
    heritage: deis
    type: api
  sessionAffinity: None
  type: ClusterIP
EOF"
