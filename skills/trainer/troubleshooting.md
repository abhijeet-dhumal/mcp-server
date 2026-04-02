# Troubleshooting Guide

Common issues and solutions for Kubeflow training jobs.

## Diagnostic Workflow

```
1. get_training_job(name)      → Check status
2. get_training_events(name)   → Check K8s events  
3. get_training_logs(name)     → Read error logs
```

## Common Issues

### Job Stuck in Pending

**Symptoms:** Job status is "Pending" for extended time.

**Diagnosis:**
```python
get_training_events(name="my-job")
```

**Common causes:**

| Event Reason | Cause | Solution |
|--------------|-------|----------|
| `Unschedulable` | No nodes with required resources | Reduce GPU/memory or wait |
| `FailedScheduling` | Node selector doesn't match | Check node labels |
| `InsufficientGPU` | Not enough GPUs | Use fewer workers |

**Solution:**
```python
# Check available resources
get_cluster_resources()

# Reduce requirements
fine_tune(..., gpu_per_worker=1, num_workers=1)
```

### OOMKilled (Out of Memory)

**Symptoms:** Pod killed with OOMKilled status.

**Diagnosis:**
```python
get_training_events(name="my-job")
# Look for: "OOMKilled" or "Evicted"
```

**Solutions:**

1. **Reduce batch size:**
```python
fine_tune(..., batch_size=2)  # Instead of 4
```

2. **Enable LoRA:**
```python
fine_tune(..., lora=True)  # Much less memory
```

3. **Use gradient checkpointing:** (in custom scripts)
```python
model.gradient_checkpointing_enable()
```

### Image Pull Errors

**Symptoms:** ImagePullBackOff or ErrImagePull.

**Diagnosis:**
```python
get_training_events(name="my-job")
# Look for: "Failed to pull image"
```

**Solutions:**

1. **Check image name:**
```python
# Correct format
run_container_training(image="docker.io/library/pytorch:2.0")
```

2. **Private registry:** Ensure imagePullSecrets are configured.

3. **Image doesn't exist:** Verify image is pushed to registry.

### CUDA Out of Memory

**Symptoms:** RuntimeError: CUDA out of memory.

**Diagnosis:**
```python
get_training_logs(name="my-job")
# Look for: "CUDA out of memory"
```

**Solutions:**

1. **Reduce batch size**
2. **Use mixed precision** (FP16/BF16)
3. **Enable gradient checkpointing**
4. **Use more GPUs with smaller batches**

### NCCL Timeout

**Symptoms:** NCCL timeout or connection refused.

**Diagnosis:**
```python
get_training_logs(name="my-job")
# Look for: "NCCL timeout" or "connection refused"
```

**Solutions:**

1. **Network policy:** Ensure pods can communicate
2. **Reduce workers:** Try single-node first
3. **Increase timeout:** Set `NCCL_TIMEOUT` env var

### HuggingFace Authentication

**Symptoms:** 401 Unauthorized for gated models.

**Diagnosis:**
```python
get_training_logs(name="my-job")
# Look for: "401" or "authentication"
```

**Solutions:**

1. **Set HF_TOKEN:**
```bash
export HF_TOKEN=hf_xxx
```

2. **Accept model license:** Visit model page on HuggingFace

### Job Failed Immediately

**Symptoms:** Job goes to "Failed" within seconds.

**Diagnosis:**
```python
get_training_logs(name="my-job", tail_lines=200)
```

**Common causes:**

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing package | Add to `packages` list |
| `SyntaxError` | Script error | Fix Python syntax |
| `FileNotFoundError` | Missing file | Check paths |

## Recovery Actions

### Retry Failed Job

```python
# Delete failed job
delete_training_job(name="failed-job")

# Resubmit with fixes
fine_tune(..., confirmed=True)
```

### Suspend and Resume

```python
# Pause to free resources
suspend_training_job(name="my-job")

# Resume later
resume_training_job(name="my-job")
```

### Clean Up

```python
# List all jobs
list_training_jobs()

# Delete completed/failed
delete_training_job(name="old-job")
```

## Getting Help

If issues persist:

1. **Collect diagnostics:**
```python
get_training_job(name="my-job")
get_training_events(name="my-job")
get_training_logs(name="my-job", tail_lines=500)
```

2. **Check cluster:**
```python
get_cluster_resources()
list_runtimes()
```

3. **Report issue** with collected information.
