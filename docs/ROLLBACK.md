# Versionamento semantico e rollback

## Versionamento

As imagens sao publicadas no GitHub Container Registry
(`ghcr.io/gaveta-cmd/integracao-continua-devops`) pelo workflow
`.github/workflows/cd.yml` ao criar uma tag `vX.Y.Z`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Cada publicacao gera as tags `1.0.0`, `1.0` e `sha-<commit>`, entao e possivel
saber exatamente qual commit originou a imagem em execucao. Uma imagem
publicada nao e alterada (artefato imutavel).

## Rollback (reverter para a versao estavel anterior)

Cenario simulado: a versao `1.1.0` foi publicada com defeito e e preciso
voltar para a `1.0.0`.

### Pelo pipeline (recomendado, auditavel)

1. GitHub > Actions > "Pipeline CD - GHCR e Deploy" > **Run workflow**.
2. Informar `version = 1.0.0` e executar. O pipeline nao reconstroi nada:
   baixa a imagem `1.0.0` do GHCR e reimplanta no ambiente de homologacao.

### No cluster (rapido)

```bash
kubectl rollout history deployment/calculadora-deployment
kubectl rollout undo deployment/calculadora-deployment
kubectl rollout status deployment/calculadora-deployment
kubectl get pods -l app=calculadora
```

### Simulacao da falha (para as evidencias)

```bash
# 1) versao boa no ar
kubectl set image deployment/calculadora-deployment calculadora=calculadora:1.0.0
# 2) "publicar" uma versao quebrada (imagem inexistente)
kubectl set image deployment/calculadora-deployment calculadora=calculadora:9.9.9-quebrada
kubectl get pods -l app=calculadora        # ImagePullBackOff / ErrImagePull
# 3) rollback
kubectl rollout undo deployment/calculadora-deployment
kubectl rollout status deployment/calculadora-deployment
kubectl get pods -l app=calculadora        # 3 pods Running na versao anterior
```

Com a estrategia padrao (RollingUpdate), os pods antigos continuam atendendo
enquanto os novos falham, entao o servico nao fica fora do ar durante o defeito.
Registrar prints de cada comando em `docs/evidencias/`.
