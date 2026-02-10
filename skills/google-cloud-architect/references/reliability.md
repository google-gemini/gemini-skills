# Reliability

[Reliability](https://cloud.google.com/architecture/framework/reliability) ensures your system can withstand and recover from failures while meeting user demand.

## Core Principles

1.  **[Define reliability goals](https://cloud.google.com/architecture/framework/reliability/define-reliability-based-on-user-experience-goals)**:
    - **SLOs (Service Level Objectives)**: Target reliability level (e.g., 99.9% availability).
    - **SLIs (Service Level Indicators)**: Metrics to measure compliance with SLO (e.g., error rate, latency).
    - **Error Budgets**: Allowed amount of unreliability. Use it to balance feature velocity vs. stability.

2.  **[Build highly available systems](https://cloud.google.com/architecture/framework/reliability/build-highly-available-systems)**:
    - **Redundancy**: Deploy across multiple **Zones** (zonal failure) and **Regions** (regional failure).
    - **Load Balancing**: Distribute traffic globally and verify health of backends.
    - **Eliminate SPOFs**: Identify and remove Single Points of Failure.

3.  **[Take advantage of horizontal scalability](https://cloud.google.com/architecture/framework/reliability/horizontal-scalability)**:
    - Scale out (add more instances) rather than up (larger instances).
    - Use **Managed Instance Groups (MIGs)** or serverless for automatic scaling.

4.  **[Design for Graceful Degradation](https://cloud.google.com/architecture/framework/reliability/graceful-degradation)**:
    - **Circuit Breakers**: Stop calling failing services to prevent cascading failures.
    - **Throttling**: Shed excess load to protect the system.
    - **Fallback**: Serve degraded functionality (e.g., cached content) instead of errors.

5.  **[Detect potential failures](https://cloud.google.com/architecture/framework/reliability/observability)**:
    - **Health Checks**: Liveness (restart if dead) and Readiness (don't send traffic until ready).
    - **Golden Signals**: Monitor Latency, Traffic, Errors, and Saturation.

6.  **[Test for Recovery](https://cloud.google.com/architecture/framework/reliability/perform-testing-for-recovery-from-failures)**:
    - **Disaster Recovery (DR)**: Regularly test RTO (Recovery Time) and RPO (Recovery Point).
    - **Chaos Engineering**: Proactively inject failures to verify resilience.
    - **Backup & Restore**: Verify backups are consistent and restorable.

## Design Review Checklist

- [ ] Are SLOs defined for critical user journeys?
- [ ] Is the architecture Multi-Zone (high availability) or Multi-Region (disaster recovery)?
- [ ] Is autoscaling configured with appropriate minimum/maximum limits?
- [ ] Are circuit breakers and retries (with exponential backoff) implemented?
- [ ] Is there a DR plan, and has it been tested recently?
- [ ] Do health checks accurately reflect service status?
