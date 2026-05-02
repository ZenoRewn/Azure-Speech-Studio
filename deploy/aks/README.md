# Azure Speech Studio on AKS

Public-internet deployment topology. All Azure keys live server-side; the
browser never sees them.

## Topology

```
Browser ──HTTPS/WSS──▶ Ingress (NGINX or AGIC, TLS + sticky cookie)
                          │
                          ▼
                  Service (ClientIP affinity, 3h timeout)
                          │
                          ▼
               Deployment (2+ pods, 1 gunicorn worker each,
                           multi-coroutine via gevent-websocket)
                          │
                          ▼
               Azure Speech / OpenAI / Voice Live APIs
```

Sticky sessions are **required** because `sessions.py` holds per-connection
state (SpeechRecognizer, PushAudioInputStream, Voice Live event loop) keyed
by SocketIO SID. A reconnect after a pod switch will re-initialise cleanly,
but in-flight conversations would be dropped.

## Quick deploy

```bash
# 0. Prereqs: kubectl, az CLI, an AKS cluster, an ACR
az aks get-credentials -g <rg> -n <aks>

# 1. Build + push
az acr login -n <acr>
docker build -t <acr>.azurecr.io/speech-studio:v1 .
docker push <acr>.azurecr.io/speech-studio:v1

# 2. Secrets (dev-grade; for prod use Key Vault + Workload Identity, see below)
kubectl create secret generic speech-studio-secrets \
  --from-literal=ASIA_SPEECH_KEY=... \
  --from-literal=ASIA_SPEECH_REGION=eastus \
  --from-literal=AZURE_OPENAI_API_KEY=... \
  --from-literal=AZURE_OPENAI_ENDPOINT=https://...openai.azure.com \
  --from-literal=AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini \
  --from-literal=AZURE_OPENAI_VERSION=2025-04-01-preview \
  --from-literal=AZURE_VOICELIVE_ENDPOINT=wss://eastus.cognitiveservices.azure.com \
  --from-literal=AZURE_STORAGE_ACCOUNT=... \
  --from-literal=AZURE_STORAGE_KEY=... \
  --from-literal=AZURE_STORAGE_CONTAINER=speech-studio

# 3. Set image in deployment.yaml or use kubectl set image
sed -i.bak 's|REGISTRY/speech-studio:TAG|<acr>.azurecr.io/speech-studio:v1|' deploy/aks/deployment.yaml

# 4. Apply
kubectl apply -f deploy/aks/deployment.yaml
kubectl apply -f deploy/aks/service.yaml
kubectl apply -f deploy/aks/ingress.yaml
kubectl apply -f deploy/aks/hpa.yaml

# 5. Watch rollout
kubectl rollout status deployment/speech-studio
kubectl get pods -l app=speech-studio -w
```

## Ingress: must-have annotations

| Concern | NGINX annotation | Why |
|---|---|---|
| WebSocket keep-alive | `proxy-read-timeout: "3600"` | Voice Live sessions often run 10+ min; default 60s kills them |
| Large uploads | `proxy-body-size: "50m"` | Voice Creation training audio + video clips |
| Sticky pod | `affinity: "cookie"` + `session-cookie-*` | Required for session-state stickiness (see above) |
| TLS | `force-ssl-redirect: "true"` | Keys travel over WSS to the server |

For **AGIC** (Application Gateway Ingress Controller), use:
- `appgw.ingress.kubernetes.io/request-timeout: "3600"`
- `appgw.ingress.kubernetes.io/cookie-based-affinity: "true"`
- `appgw.ingress.kubernetes.io/connection-draining: "true"`

(Example block provided commented-out in `ingress.yaml`.)

## Production: Azure Key Vault + Workload Identity

Do **not** ship real keys in a `Secret` manifest in git. The recommended pattern:

1. Enable Workload Identity on the AKS cluster:
   ```bash
   az aks update -g <rg> -n <aks> --enable-oidc-issuer --enable-workload-identity
   ```
2. Create a managed identity federated to the service account used by the
   Deployment, grant it `get` on the Key Vault secrets.
3. Install the Secrets Store CSI driver + Azure provider.
4. Apply a `SecretProviderClass` (see commented block in
   `secret-example.yaml`) that syncs Key Vault → a Kubernetes Secret.
5. Reference that Secret via `envFrom.secretRef` in the Deployment — no
   manifest changes needed.

## Scaling considerations

- **Horizontal only.** Each pod runs 1 gunicorn worker. Do not raise `-w`
  without also replacing the in-memory `SessionManager` with Redis.
- **Redis for multi-worker SocketIO** (future): install Flask-SocketIO with
  `message_queue="redis://..."` and point all replicas at the same queue to
  share event broadcasts. Not needed for sticky-session deployments.
- **Connection draining.** `terminationGracePeriodSeconds: 60` plus a 30s
  `preStop sleep` gives in-flight WebSocket sessions time to finish.
- **Voice Live per-pod ceiling.** Each Voice Live connection spins up an
  asyncio event loop; size `resources.limits` accordingly. Target ~10
  concurrent Voice Live sessions per 1 vCPU / 1 Gi pod as a starting point
  and tune from load tests.

## Verification checklist

After `kubectl apply`:

- `kubectl get pods` → all `1/1 Running`
- `kubectl exec <pod> -- curl -s http://localhost:5001/healthz` → `{"status":"ok"}`
- Browser at `https://speech-studio.example.com` loads the Aurora UI
- Open Voice Live tab, start a 3-minute conversation — verify it does not
  drop at the 60s mark (would indicate Ingress timeout misconfigured)
- Refresh the page mid-session — same pod should serve (check
  `speech-studio-affinity` cookie in browser devtools)
- Scale down one pod: `kubectl scale deployment/speech-studio --replicas=1`
  → other clients reconnect cleanly within seconds

