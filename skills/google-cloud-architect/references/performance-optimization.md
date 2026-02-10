# Performance Optimization

[Performance Optimization](https://cloud.google.com/architecture/framework/performance-optimization) ensures your resources scale efficiently to meet system requirements.

## Core Principles

1.  **[Plan resource allocation](https://cloud.google.com/architecture/framework/performance-optimization/plan-resource-allocation)**:
    - **Workload Requirements**: Understand if workload is CPU, Memory, or I/O bound.
    - **Machine Types**:
      - _E2/N2D_: General purpose.
      - _C2/C3_: Compute-optimized (HPC, Gaming).
      - _M1/M2_: Memory-optimized (SAP HANA, large in-memory DBs).
    - **Quotas**: PROACTIVELY request quota increases before launch.

2.  **[Take advantage of Elasticity](https://cloud.google.com/architecture/framework/performance-optimization/elasticity)**:
    - **Predictive Autoscaling**: Scale out _before_ the load arrives based on historical patterns.
    - **Serverless**: Use Cloud Run or Cloud Functions for instant scaling from zero.
    - **GKE Autopilot**: Let Google manage node scaling and bin-packing.

3.  **[Promote Modular Design](https://cloud.google.com/architecture/framework/performance-optimization/promote-modular-design)**:
    - **Microservices**: Scale components independently based on their specific bottlenecks.
    - **Loose Coupling**: Use Pub/Sub to decouple producers from consumers, buffering traffic spikes.
    - **Concurrency**: Process multiple requests per instance (Cloud Run concurrency settings).

4.  **[Continuously monitor and improve](https://cloud.google.com/architecture/framework/performance-optimization/continuously-monitor-and-improve-performance)**:
    - **Cloud Profiler**: Continuous CPU/Heap profiling with low overhead to identify "hot" code paths.
    - **Cloud Trace**: Distributed tracing to find latency bottlenecks in microservices.
    - **Performance Dashboard**: Visualize packet loss and latency between regions.

## Optimization Techniques

### Compute & Network

- **Cloud CDN**: Cache static assets at the edge.
- **Load Balancing**: Use Global External Application Load Balancer for closest-entry routing (Anycast IP).
- **Protocol**: Use HTTP/3 (QUIC) or gRPC for efficient communication.

### Database & Storage

- **Caching**: Use **Memorystore** (Redis/Memcached) for high-frequency reads.
- **Read Replicas**: Offload read traffic from the primary database instance (Cloud SQL).
- **Sharding**: Distribute write load across multiple instances (Spanner does this automatically).
- **Disk Type**: Use Local SSD for temporary scratch space (extreme IOPS) or PD-Extreme.

## Design Review Checklist

- [ ] Is the machine type validated against workload benchmarks?
- [ ] Is caching (CDN/Redis) implemented for static or frequent content?
- [ ] Is the database optimized (indexes, replicas, sharding)?
- [ ] Are quotas sufficient for peak load?
- [ ] Is profiling enabled to detect code-level inefficiencies?
