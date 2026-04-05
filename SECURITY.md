# Security Policy

## Project Status

This project is in **early development** and has not yet reached a stable release (1.0). The API and features may change between versions.

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| 0.x     | ✅ Yes    | Pre-release, actively developed |

Once the project reaches 1.0, a formal support policy for stable releases will be established.

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### GitHub Security Advisories (Preferred)

1. Go to the [Security tab](https://github.com/kubeflow/mcp-server/security)
2. Click "Report a vulnerability"
3. Fill out the form with details

### What to Include

- Type of vulnerability (e.g., injection, authentication bypass)
- Location of the affected code (file path, line number)
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity (critical: ASAP, high: 2 weeks, medium: 1 month)

## Security Considerations

### Current Security Measures

1. **Input Validation**: All tool inputs are validated and sanitized
2. **Namespace Isolation**: Jobs are scoped to user-specified namespaces
3. **No Credential Storage**: Server doesn't store Kubernetes credentials
4. **Preview Mode**: Destructive operations require explicit confirmation

### Known Limitations

1. **No Authentication**: Current version has no built-in auth (use network policies)
2. **No Authorization**: All tools accessible to all users (use persona filters as workaround)
3. **Audit Logging**: Not yet implemented

### Recommended Deployment Practices

```yaml
# 1. Run in isolated namespace
apiVersion: v1
kind: Namespace
metadata:
  name: kubeflow-mcp
  labels:
    pod-security.kubernetes.io/enforce: restricted

# 2. Use NetworkPolicy to restrict access
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-server-ingress
spec:
  podSelector:
    matchLabels:
      app: kubeflow-mcp
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              trusted: "true"
      ports:
        - port: 8000

# 3. Use ServiceAccount with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubeflow-mcp
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: kubeflow-mcp-role
rules:
  - apiGroups: ["trainer.kubeflow.org"]
    resources:
      - trainjobs
      - trainingruntimes
      - clustertrainingruntimes
    verbs: ["get", "list", "create", "delete", "patch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "events"]
    verbs: ["get", "list"]
```

## Security Roadmap

See [ROADMAP.md](ROADMAP.md) for planned security enhancements:
- Bearer token authentication
- OAuth 2.1 + PKCE
- Audit logging
- Rate limiting
