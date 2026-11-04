# Evidências da A2

Registro dos cenários executados no Kubernetes local (Docker Desktop), com a
saída real dos comandos: subida, autocura, balanceamento e escala,
persistência do histórico e rollback. Os comandos são os do roteiro em
[A2-tarefas.md](../A2-tarefas.md) e [ROLLBACK.md](../ROLLBACK.md).

O valor do `ADMIN_TOKEN` usado abaixo é apenas de teste local. O secret real
fica no GitHub Secrets.

## Pipeline de CD no GitHub Actions

| Execução | Resultado |
|---|---|
| Tag `v1.0.0` (push) | Testes: sucesso. Publicação da imagem no GHCR: sucesso. Deploy de homologação: falhou por nome do cluster `kind` (corrigido no PR #10; ver o post-mortem no README) |
| Execução manual com `version = 1.0.0` (rollback/reimplantação) | Deploy de homologação: sucesso (imagem baixada do GHCR, manifestos aplicados e teste de fumaça aprovado) |

Imagem publicada: `ghcr.io/gaveta-cmd/integracao-continua-devops`, com as tags
`1.0.0`, `1.0`, `sha-<commit>` e `latest`.

## 0. Ambiente

Execução em 04/11/2026 01:27 no Docker Desktop com Kubernetes (cluster local de 1 nó), a partir da branch `main`.

```console
$ git log -1 --format="%h %s"
53437c5 Merge pull request #10 from Gaveta-cmd/fix/cd-kind-cluster
```

```console
$ docker --version
Docker version 29.5.3, build d1c06ef
```

```console
$ kubectl get nodes
NAME                    STATUS   ROLES           AGE   VERSION
desktop-control-plane   Ready    control-plane   59m   v1.34.3
```


## 1. Build da imagem

```console
$ docker build -t calculadora:1.0.0 . 2>&1 | tail -4
#11 exporting manifest list sha256:e624d6cbb894628c9ffc4fc4a927afa28b926f26cb1780b4cb715793524c6ef4 0.0s done
#11 naming to docker.io/library/calculadora:1.0.0 done
#11 unpacking to docker.io/library/calculadora:1.0.0 0.0s done
#11 DONE 0.2s
```

```console
$ docker images calculadora
IMAGE               ID             DISK USAGE   CONTENT SIZE   EXTRA
calculadora:1.0.0   e624d6cbb894         84MB         20.4MB        
```


## 2. Subida no Kubernetes (3 réplicas)

```console
$ kubectl create secret generic app-secret --from-literal=ADMIN_TOKEN=valor-de-teste-local
secret/app-secret created
```

```console
$ kubectl apply -f k8s/
configmap/app-config created
deployment.apps/calculadora-deployment created
service/calculadora-service created
persistentvolumeclaim/historico-pvc created
```

```console
$ kubectl set image deployment/calculadora-deployment calculadora=calculadora:1.0.0
deployment.apps/calculadora-deployment image updated
```

```console
$ kubectl rollout status deployment/calculadora-deployment --timeout=150s
Waiting for deployment "calculadora-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "calculadora-deployment" rollout to finish: 1 old replicas are pending termination...
deployment "calculadora-deployment" successfully rolled out
```

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS    RESTARTS   AGE
calculadora-deployment-849f6d6c59-kllb4   1/1     Running   0          47s
calculadora-deployment-849f6d6c59-lx6zj   1/1     Running   0          58s
calculadora-deployment-849f6d6c59-zp5tw   1/1     Running   0          40s
```

```console
$ kubectl get svc,pvc
NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/calculadora-service   NodePort    10.96.99.243   <none>        8080:30080/TCP   59s
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP          60m

NAME                                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/historico-pvc   Bound    pvc-dea1fcfe-7783-4ae0-8bba-952485311fe3   1Gi        RWO            standard       <unset>                 58s
```

```console
$ kubectl exec $POD -- python -c 'import urllib.request as u;print(u.urlopen("http://calculadora-service:8080/healthz").read().decode())'
ok
```


## 3. Autocura (self-healing)

Um pod é apagado à mão; o Deployment detecta a divergência e cria outro, voltando às 3 réplicas.

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS    RESTARTS   AGE
calculadora-deployment-849f6d6c59-kllb4   1/1     Running   0          49s
calculadora-deployment-849f6d6c59-lx6zj   1/1     Running   0          60s
calculadora-deployment-849f6d6c59-zp5tw   1/1     Running   0          42s
```

```console
$ kubectl delete pod calculadora-deployment-849f6d6c59-kllb4 --wait=false
pod "calculadora-deployment-849f6d6c59-kllb4" deleted from default namespace
```

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS        RESTARTS   AGE
calculadora-deployment-849f6d6c59-5729j   0/1     Running       0          3s
calculadora-deployment-849f6d6c59-kllb4   1/1     Terminating   0          53s
calculadora-deployment-849f6d6c59-lx6zj   1/1     Running       0          64s
calculadora-deployment-849f6d6c59-zp5tw   1/1     Running       0          46s
```

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS    RESTARTS   AGE
calculadora-deployment-849f6d6c59-5729j   1/1     Running   0          33s
calculadora-deployment-849f6d6c59-lx6zj   1/1     Running   0          94s
calculadora-deployment-849f6d6c59-zp5tw   1/1     Running   0          76s
```


## 4. Balanceamento e escala (3 para 5 réplicas)

O Service distribui as requisições entre os pods. A contagem mostra quantas das 30 requisições cada pod atendeu.

```console
$ kubectl exec $POD -- sh -c 'for i in $(seq 1 30); do wget -qO- http://calculadora-service:8080/api/info; echo; done' | sort | uniq -c
     10 {"pod": "calculadora-deployment-849f6d6c59-5729j"}
      8 {"pod": "calculadora-deployment-849f6d6c59-lx6zj"}
     12 {"pod": "calculadora-deployment-849f6d6c59-zp5tw"}
```

```console
$ kubectl scale deployment/calculadora-deployment --replicas=5
deployment.apps/calculadora-deployment scaled
```

```console
$ kubectl rollout status deployment/calculadora-deployment --timeout=120s
Waiting for deployment "calculadora-deployment" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "calculadora-deployment" rollout to finish: 4 of 5 updated replicas are available...
deployment "calculadora-deployment" successfully rolled out
```

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS    RESTARTS   AGE
calculadora-deployment-849f6d6c59-5729j   1/1     Running   0          54s
calculadora-deployment-849f6d6c59-6hgtd   1/1     Running   0          20s
calculadora-deployment-849f6d6c59-fnv6t   1/1     Running   0          20s
calculadora-deployment-849f6d6c59-lx6zj   1/1     Running   0          115s
calculadora-deployment-849f6d6c59-zp5tw   1/1     Running   0          97s
```

```console
$ kubectl exec $POD -- sh -c 'for i in $(seq 1 30); do wget -qO- http://calculadora-service:8080/api/info; echo; done' | sort | uniq -c
      8 {"pod": "calculadora-deployment-849f6d6c59-5729j"}
      9 {"pod": "calculadora-deployment-849f6d6c59-6hgtd"}
      3 {"pod": "calculadora-deployment-849f6d6c59-fnv6t"}
      5 {"pod": "calculadora-deployment-849f6d6c59-lx6zj"}
      5 {"pod": "calculadora-deployment-849f6d6c59-zp5tw"}
```


## 5. Persistência do histórico (PVC)

Uma conta é gravada por um pod, lida por outros e, depois, todos os pods são apagados. O histórico continua, pois fica no volume.

```console
$ kubectl exec $POD -- python -c 'import urllib.request as u,json;r=u.Request("http://calculadora-service:8080/api/calcular",data=json.dumps({"operacao":"soma","a":40,"b":2}).encode(),headers={"Content-Type":"application/json"});print(u.urlopen(r).read().decode())'
{"operacao": "soma", "a": 40, "b": 2, "resultado": 42, "pod": "calculadora-deployment-849f6d6c59-fnv6t"}
```

```console
$ for i in 1 2 3 4 5 6; do kubectl exec $POD -- python -c 'import urllib.request as u;print(u.urlopen("http://calculadora-service:8080/api/historico").read().decode())'; done | sort | uniq -c
      6 [{"operacao": "soma", "a": 40, "b": 2, "resultado": 42}]
```

```console
$ kubectl delete pods -l app=calculadora --wait=false
pod "calculadora-deployment-849f6d6c59-5729j" deleted from default namespace
pod "calculadora-deployment-849f6d6c59-6hgtd" deleted from default namespace
pod "calculadora-deployment-849f6d6c59-fnv6t" deleted from default namespace
pod "calculadora-deployment-849f6d6c59-lx6zj" deleted from default namespace
pod "calculadora-deployment-849f6d6c59-zp5tw" deleted from default namespace
```

```console
$ kubectl rollout status deployment/calculadora-deployment --timeout=120s
deployment "calculadora-deployment" successfully rolled out
```

```console
$ kubectl exec $POD -- python -c 'import urllib.request as u;print(u.urlopen("http://calculadora-service:8080/api/historico").read().decode())'
[{"operacao": "soma", "a": 40, "b": 2, "resultado": 42}]
```


## 6. Versionamento e rollback

Uma versão com defeito (imagem inexistente) é publicada. O RollingUpdate mantém os pods antigos no ar enquanto os novos falham; depois o rollback volta para a versão estável.

```console
$ kubectl scale deployment/calculadora-deployment --replicas=3
deployment.apps/calculadora-deployment scaled
```

```console
$ kubectl rollout status deployment/calculadora-deployment --timeout=120s
deployment "calculadora-deployment" successfully rolled out
```

```console
$ kubectl get deployment calculadora-deployment -o jsonpath="{.spec.template.spec.containers[0].image}"; echo
calculadora:1.0.0
```

```console
$ kubectl set image deployment/calculadora-deployment calculadora=calculadora:9.9.9-quebrada
deployment.apps/calculadora-deployment image updated
```

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS             RESTARTS   AGE
calculadora-deployment-7f9cc65ff9-kmhdk   0/1     ImagePullBackOff   0          25s
calculadora-deployment-849f6d6c59-g68pc   1/1     Running            0          94s
calculadora-deployment-849f6d6c59-xvcsn   1/1     Running            0          94s
calculadora-deployment-849f6d6c59-zmj67   1/1     Running            0          94s
```

Mesmo com a versão quebrada, o serviço continua respondendo pelos pods antigos:

```console
$ kubectl exec $OK -- python -c 'import urllib.request as u;print(u.urlopen("http://calculadora-service:8080/healthz").read().decode())'
ok
```

```console
$ kubectl rollout history deployment/calculadora-deployment
deployment.apps/calculadora-deployment 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>

```

Rollback:

```console
$ kubectl rollout undo deployment/calculadora-deployment
deployment.apps/calculadora-deployment rolled back
```

```console
$ kubectl rollout status deployment/calculadora-deployment --timeout=120s
deployment "calculadora-deployment" successfully rolled out
```

```console
$ kubectl get pods -l app=calculadora
NAME                                      READY   STATUS    RESTARTS   AGE
calculadora-deployment-849f6d6c59-g68pc   1/1     Running   0          100s
calculadora-deployment-849f6d6c59-xvcsn   1/1     Running   0          100s
calculadora-deployment-849f6d6c59-zmj67   1/1     Running   0          100s
```

```console
$ kubectl get deployment calculadora-deployment -o jsonpath="{.spec.template.spec.containers[0].image}"; echo
calculadora:1.0.0
```


## 7. Limpeza

```console
$ kubectl delete -f k8s/
configmap "app-config" deleted from default namespace
deployment.apps "calculadora-deployment" deleted from default namespace
service "calculadora-service" deleted from default namespace
persistentvolumeclaim "historico-pvc" deleted from default namespace
```

```console
$ kubectl delete secret app-secret
secret "app-secret" deleted from default namespace
```

```console
$ kubectl get pods,svc,pvc
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   63m
```
