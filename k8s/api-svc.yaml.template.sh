APP=$1
eval "cat <<EOF
apiVersion: v1
kind: Service
metadata:
  name: api
  labels:
    app: ${APP}
spec:
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 8000
  selector:
    app: ${APP}
    type: api
  type: ClusterIP
EOF"
