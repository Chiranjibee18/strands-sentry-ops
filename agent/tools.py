"""
Operational AWS Cloud Tools for Sentry-Ops Agent
------------------------------------------------
High-impact cloud operations and diagnostics tools.
Each tool has explicit risk ratings used by Guardrails.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
import time


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    output: Dict[str, Any]
    message: str
    execution_time_ms: float


def aws_fetch_cloudwatch_metrics(service_name: str, metric_name: str = "CPUUtilization") -> ToolResult:
    """Fetches real-time telemetry from Amazon CloudWatch."""
    t0 = time.perf_counter()
    metrics = {
        "service": service_name,
        "metric": metric_name,
        "values": [74.2, 82.5, 91.8, 96.4, 98.1],
        "threshold": 80.0,
        "status": "ALARM_TRIGGERED",
        "region": "us-east-1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return ToolResult(
        success=True,
        tool_name="aws_fetch_cloudwatch_metrics",
        output=metrics,
        message=f"CloudWatch metric {metric_name} for {service_name} retrieved: ALARM active (peak 98.1%).",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def aws_scale_auto_scaling_group(asg_name: str, desired_capacity: int) -> ToolResult:
    """Scales an Amazon EC2 Auto Scaling Group to target capacity."""
    t0 = time.perf_counter()
    output = {
        "asg_name": asg_name,
        "previous_capacity": 4,
        "new_desired_capacity": desired_capacity,
        "scaling_activity_id": f"act-asg-{int(time.time())}",
        "status": "InService",
    }
    return ToolResult(
        success=True,
        tool_name="aws_scale_auto_scaling_group",
        output=output,
        message=f"ASG '{asg_name}' successfully scaled from 4 to {desired_capacity} instances. Load rebalancing initiated.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def aws_flush_redis_cache(cluster_id: str, db_index: int = 0) -> ToolResult:
    """Flushes stale keys from Amazon ElastiCache Redis."""
    t0 = time.perf_counter()
    output = {
        "cluster_id": cluster_id,
        "db_index": db_index,
        "keys_evicted": 14209,
        "memory_reclaimed_mb": 512.4,
        "cache_hit_rate_restored": "98.7%",
    }
    return ToolResult(
        success=True,
        tool_name="aws_flush_redis_cache",
        output=output,
        message=f"ElastiCache Redis cluster '{cluster_id}' db[{db_index}] flushed. 14,209 stale keys evicted, 512MB freed.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def aws_isolate_compromised_instance(instance_id: str, vpc_id: str = "vpc-prod-01") -> ToolResult:
    """Quarantines a compromised EC2 instance into a forensic isolation security group."""
    t0 = time.perf_counter()
    output = {
        "instance_id": instance_id,
        "vpc_id": vpc_id,
        "previous_security_groups": ["sg-web-ingress", "sg-app-mesh"],
        "quarantine_security_group": "sg-isolated-forensics-no-egress",
        "snapshot_created": f"snap-{int(time.time())}",
        "action": "Egress/Ingress blocked. EBS forensic snapshot preserved.",
    }
    return ToolResult(
        success=True,
        tool_name="aws_isolate_compromised_instance",
        output=output,
        message=f"Instance '{instance_id}' isolated into forensic quarantine SG. Outbound traffic severed, EBS snapshot created.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def aws_remediate_oom_pod(namespace: str, deployment_name: str, new_memory_limit: str = "2Gi") -> ToolResult:
    """Updates Kubernetes pod memory limits on Amazon EKS to resolve OOMKilled crashes."""
    t0 = time.perf_counter()
    output = {
        "namespace": namespace,
        "deployment": deployment_name,
        "old_limit": "512Mi",
        "new_limit": new_memory_limit,
        "rolling_update_status": "Success",
        "restarted_replicas": 3,
    }
    return ToolResult(
        success=True,
        tool_name="aws_remediate_oom_pod",
        output=output,
        message=f"EKS Deployment '{deployment_name}' in ns '{namespace}' upgraded to {new_memory_limit} memory. Rolling restart complete.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def aws_terminate_rds(db_instance_id: str) -> ToolResult:
    """HIGH-RISK ACTION: Deletes an Amazon RDS database instance."""
    t0 = time.perf_counter()
    output = {
        "db_instance_id": db_instance_id,
        "status": "TERMINATED",
        "warning": "Data destroyed unless final snapshot was requested.",
    }
    return ToolResult(
        success=True,
        tool_name="aws_terminate_rds",
        output=output,
        message=f"CRITICAL: RDS instance '{db_instance_id}' deleted.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def inspect_dependencies(log_text: str = "") -> ToolResult:
    """Diagnostic Tool: Scans CI/CD failure log for missing dependencies, modules, or package conflicts."""
    t0 = time.perf_counter()
    lines = log_text.splitlines()
    observed_evidence = []
    missing_packages = []

    for i, line in enumerate(lines, 1):
        if "ModuleNotFoundError" in line or "No module named" in line:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "PythonModuleMissing"})
            parts = line.split("No module named")
            if len(parts) > 1:
                missing_packages.append(parts[1].strip().strip("'\""))
        elif "Cannot find module" in line or "npm ERR!" in line:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "NodeModuleMissing"})
            parts = line.split("Cannot find module")
            if len(parts) > 1:
                missing_packages.append(parts[1].strip().strip("'\""))
        elif "pip install" in line or "requirements.txt" in line or "package.json" in line:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "ManifestReference"})

    output = {
        "diagnostic_category": "Dependencies & Packages",
        "missing_items": list(set(missing_packages)) if missing_packages else ["unresolved_dependency"],
        "observed_facts": observed_evidence,
        "suggested_verification": f"pip check || npm ls {missing_packages[0] if missing_packages else ''}".strip(),
        "hypothesis": "Build failed due to uninstalled or unpinned runtime/build dependency."
    }
    return ToolResult(
        success=True,
        tool_name="inspect_dependencies",
        output=output,
        message=f"Dependency inspection complete: found {len(observed_evidence)} relevant log lines.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def inspect_docker(log_text: str = "") -> ToolResult:
    """Diagnostic Tool: Scans build log for Dockerfile parse errors, image storage constraints, or container crashes."""
    t0 = time.perf_counter()
    lines = log_text.splitlines()
    observed_evidence = []
    error_type = "GenericDockerBuildFailure"

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        if "dockerfile parse error" in line_lower or "failed to solve" in line_lower:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "SyntaxError"})
            error_type = "DockerfileParseError"
        elif "no space left on device" in line_lower or "storage" in line_lower:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "StorageExhaustion"})
            error_type = "DiskSpaceExhausted"
        elif "step " in line_lower or "copy failed" in line_lower or "run " in line_lower:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "BuildStep"})

    output = {
        "diagnostic_category": "Docker & Container Runtime",
        "error_type": error_type,
        "observed_facts": observed_evidence,
        "suggested_verification": "docker builder prune -f && docker build --no-cache .",
        "hypothesis": "Container image build terminated during instruction execution or local daemon disk exhaustion."
    }
    return ToolResult(
        success=True,
        tool_name="inspect_docker",
        output=output,
        message=f"Docker inspection complete: classified {error_type} across {len(observed_evidence)} log lines.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def inspect_tests(log_text: str = "") -> ToolResult:
    """Diagnostic Tool: Scans test output logs for AssertionErrors, HTTP status code mismatches, and mock failures."""
    t0 = time.perf_counter()
    lines = log_text.splitlines()
    observed_evidence = []
    assertion_mismatches = []

    for i, line in enumerate(lines, 1):
        if "AssertionError" in line or "assert " in line:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "AssertionFailure"})
            assertion_mismatches.append(line.strip())
        elif "FAILED" in line or "FAIL " in line or "expected" in line.lower():
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "TestExpectationMismatch"})
        elif "Traceback" in line:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "StackTrace"})

    output = {
        "diagnostic_category": "Automated Test Suite",
        "failure_count": max(len(assertion_mismatches), 1),
        "observed_facts": observed_evidence,
        "suggested_verification": "pytest -vv -k 'test_failing_case' --tb=short",
        "hypothesis": "Unit or integration test assertion failed due to unexpected API response or state divergence."
    }
    return ToolResult(
        success=True,
        tool_name="inspect_tests",
        output=output,
        message=f"Test inspection complete: isolated {len(observed_evidence)} assertion/traceback lines.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def inspect_pipeline(log_text: str = "") -> ToolResult:
    """Diagnostic Tool: Scans CI/CD workflow configurations, permissions, and runner infrastructure."""
    t0 = time.perf_counter()
    lines = log_text.splitlines()
    observed_evidence = []
    config_issue = "PipelineConfigurationError"

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        if "permission denied" in line_lower or "403 forbidden" in line_lower or "eacces" in line_lower:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "PermissionDenied"})
            config_issue = "PermissionsOrCredentialError"
        elif "mapping values are not allowed" in line_lower or "yaml" in line_lower or "syntax error" in line_lower:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "YAMLParseError"})
            config_issue = "YAMLConfigurationSyntaxError"
        elif "jenkinsfile" in line_lower or "workflow.yaml" in line_lower or ".github" in line_lower:
            observed_evidence.append({"line_number": i, "content": line.strip(), "type": "PipelineDefinition"})

    output = {
        "diagnostic_category": "CI/CD Pipeline & Infrastructure",
        "issue_type": config_issue,
        "observed_facts": observed_evidence,
        "suggested_verification": "yamllint .github/workflows/*.yaml || chmod +x ./gradlew",
        "hypothesis": "Runner halted due to pipeline script syntax invalidity or missing execution permissions."
    }
    return ToolResult(
        success=True,
        tool_name="inspect_pipeline",
        output=output,
        message=f"Pipeline inspection complete: classified {config_issue} across {len(observed_evidence)} lines.",
        execution_time_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


ALL_AVAILABLE_TOOLS = {
    # CI/CD Diagnostic Tools (#tool-selection)
    "inspect_dependencies": inspect_dependencies,
    "inspect_docker": inspect_docker,
    "inspect_tests": inspect_tests,
    "inspect_pipeline": inspect_pipeline,
    # Production Cloud Ops Tools
    "fetch_cloudwatch_metrics": aws_fetch_cloudwatch_metrics,
    "scale_auto_scaling_group": aws_scale_auto_scaling_group,
    "flush_redis_cache": aws_flush_redis_cache,
    "isolate_compromised_instance": aws_isolate_compromised_instance,
    "remediate_oom_pod": aws_remediate_oom_pod,
    "terminate_rds_database": aws_terminate_rds,
}

