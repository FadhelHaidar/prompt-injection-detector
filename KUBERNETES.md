# Kubernetes Deployment Guide

This guide covers deploying, monitoring, and managing the Prompt Injection Detector on local Kubernetes (Docker Desktop).

## Prerequisites

1. **Docker Desktop** with Kubernetes enabled
   - Settings → Kubernetes → Enable Kubernetes → Apply & Restart
   - Wait 2-3 minutes for Kubernetes to start

2. **Verify setup:**
   ```cmd
   kubectl version --client
   kubectl cluster-info
   ```

## Deployment

### Step 1: Build the Docker Image

Build the image locally:
```cmd
docker build -t prompt-injection-detector:latest .
```

Verify the image:
```cmd
docker images | findstr prompt-injection-detector
```

### Step 2: Deploy to Kubernetes

Apply the Kubernetes manifests:
```cmd
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Step 3: Verify Deployment

Check if pods are running:
```cmd
kubectl get pods -l app=prompt-injection-detector
```

Expected output:
```
NAME                                        READY   STATUS    RESTARTS   AGE
prompt-injection-detector-xxxxxxxxx-xxxxx   1/1     Running   0          30s
```

Watch pod status in real-time:
```cmd
kubectl get pods -l app=prompt-injection-detector -w
```

### Step 4: Access the Application

Forward the service to localhost:
```cmd
kubectl port-forward svc/prompt-injection-detector 8000:8000
```

Keep this terminal open. Access the application:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health/live
- **Readiness Check**: http://localhost:8000/health/ready

Stop port-forwarding with `Ctrl+C`.

## Monitoring

### View Logs

**Real-time logs:**
```cmd
kubectl logs -l app=prompt-injection-detector -f
```

**Last 50 lines:**
```cmd
kubectl logs -l app=prompt-injection-detector --tail=50
```

**Logs from specific pod:**
```cmd
kubectl logs <pod-name>
```

**Previous pod logs (if crashed):**
```cmd
kubectl logs <pod-name> --previous
```

### Check Pod Status

**Basic status:**
```cmd
kubectl get pods -l app=prompt-injection-detector
```

**Detailed information:**
```cmd
kubectl describe pod -l app=prompt-injection-detector
```

**All resources:**
```cmd
kubectl get all -l app=prompt-injection-detector
```

### Check Events

View recent cluster events:
```cmd
kubectl get events --sort-by='.lastTimestamp'
```

Filter by your app:
```cmd
kubectl get events --field-selector involvedObject.name=<pod-name>
```

### Resource Usage (Requires Metrics Server)

**Install metrics-server:**
```cmd
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**Configure for Docker Desktop:**
```cmd
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

**Wait ~30 seconds, then check:**
```cmd
kubectl top nodes
kubectl top pods
```

**View resource usage for your app:**
```cmd
kubectl top pods -l app=prompt-injection-detector
```

## Management

### Scale Manually

Increase replicas:
```cmd
kubectl scale deployment/prompt-injection-detector --replicas=3
```

Decrease replicas:
```cmd
kubectl scale deployment/prompt-injection-detector --replicas=1
```

Check current scale:
```cmd
kubectl get deployment prompt-injection-detector
```

### Restart Deployment

Rolling restart (zero downtime):
```cmd
kubectl rollout restart deployment/prompt-injection-detector
```

Check rollout status:
```cmd
kubectl rollout status deployment/prompt-injection-detector
```

### Update the Application

After code changes:

1. Rebuild image:
   ```cmd
   docker build -t prompt-injection-detector:latest .
   ```

2. Restart pods to use new image:
   ```cmd
   kubectl rollout restart deployment/prompt-injection-detector
   ```

3. Watch the rollout:
   ```cmd
   kubectl rollout status deployment/prompt-injection-detector
   ```

### Shell Access

Get a shell inside a running pod:
```cmd
kubectl exec -it <pod-name> -- /bin/bash
```

Run a command without entering shell:
```cmd
kubectl exec <pod-name> -- ls -la /app
```

## Troubleshooting

### Pod Not Starting

**Check pod status:**
```cmd
kubectl describe pod <pod-name>
```

**Common issues:**
- `ImagePullBackOff`: Image not found locally
  - Solution: Rebuild image with correct tag
- `CrashLoopBackOff`: Application crashes on startup
  - Solution: Check logs with `kubectl logs <pod-name>`
- `Pending`: Insufficient resources
  - Solution: Check `kubectl describe node`

### Cannot Connect to Service

**Verify service exists:**
```cmd
kubectl get svc prompt-injection-detector
```

**Test service from inside cluster:**
```cmd
kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -- curl http://prompt-injection-detector:8000/health/live
```

**Use port-forward as fallback:**
```cmd
kubectl port-forward svc/prompt-injection-detector 8000:8000
```

### High Memory Usage

**Check current usage:**
```cmd
kubectl top pods -l app=prompt-injection-detector
```

**Increase memory limit:**
Edit `k8s/deployment.yaml` and increase `resources.limits.memory`, then:
```cmd
kubectl apply -f k8s/deployment.yaml
```

### View All Resources

```cmd
kubectl get all -l app=prompt-injection-detector -o wide
```

## Shutdown

### Stop Port-Forwarding

Press `Ctrl+C` in the terminal running port-forward.

### Delete Deployment

**Delete using manifest files:**
```cmd
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml
```

**Or delete by label:**
```cmd
kubectl delete all -l app=prompt-injection-detector
```

### Verify Cleanup

```cmd
kubectl get all -l app=prompt-injection-detector
```

Should return: `No resources found`

### Remove Docker Image (Optional)

```cmd
docker rmi prompt-injection-detector:latest
```

### Full Reset

If you need to completely reset:
```cmd
kubectl delete all --all
docker system prune -a
```

**Warning**: This removes ALL Kubernetes resources and Docker images.

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Build image | `docker build -t prompt-injection-detector:latest .` |
| Deploy | `kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml` |
| View pods | `kubectl get pods -l app=prompt-injection-detector` |
| View logs | `kubectl logs -l app=prompt-injection-detector -f` |
| Port forward | `kubectl port-forward svc/prompt-injection-detector 8000:8000` |
| Scale | `kubectl scale deployment/prompt-injection-detector --replicas=N` |
| Restart | `kubectl rollout restart deployment/prompt-injection-detector` |
| Shell access | `kubectl exec -it <pod-name> -- /bin/bash` |
| Delete | `kubectl delete all -l app=prompt-injection-detector` |

### Useful Kubectl Flags

- `-f`: Follow logs
- `-w`: Watch resources
- `-o wide`: More detailed output
- `-o yaml`: YAML output
- `-o json`: JSON output
- `--tail=N`: Show last N lines of logs
- `--previous`: Show logs from previous container

## Next Steps

- **Add autoscaling**: Create HPA manifest for automatic scaling
- **Add ingress**: Configure ingress controller for custom hostname
- **Add monitoring**: Set up Prometheus/Grafana for metrics
- **Add persistence**: Use PersistentVolumes for model cache
- **Production deployment**: Push to cloud Kubernetes (AKS, EKS, GKE)
