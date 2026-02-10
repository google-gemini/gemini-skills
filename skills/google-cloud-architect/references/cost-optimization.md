# Cost Optimization

[Cost Optimization](https://cloud.google.com/architecture/framework/cost-optimization) minimizes waste while maximizing the business value of your cloud investment.

## Core Principles

1.  **[Align cloud spending with business value](https://cloud.google.com/architecture/framework/cost-optimization/align-cloud-spending-business-value)**:
    - **FinOps**: Collaboration between Engineering, Finance, and Business.
    - **Unit Economics**: Measure cost per transaction/user/order.
    - **TCO**: Consider Total Cost of Ownership, including operational overhead (managed services often lower TCO).

2.  **[Foster a culture of cost awareness](https://cloud.google.com/architecture/framework/cost-optimization/foster-culture-cost-awareness)**:
    - **Visibility**: Show engineers the cost of their resources (BigQuery export to Looker).
    - **Budgets & Alerts**: Set up Pub/Sub notifications or email alerts when spending exceeds thresholds.
    - **Labels**: Tag resources (Environment, CostCenter, Owner) for granular cost allocation.

3.  **[Optimize resource usage](https://cloud.google.com/architecture/framework/cost-optimization/optimize-resource-usage)**:
    - **Right-sizing**: Adjust VM/database size based on utilization metrics. Avoid over-provisioning.
    - **Autoscaling**: Scale to zero (Cloud Run) or minimum instances during off-peak.
    - **Storage Classes**: Automate lifecycle management (Standard -> Nearline -> Coldline -> Archive).

4.  **[Optimize Continuously](https://cloud.google.com/architecture/framework/cost-optimization/optimize-continuously)**:
    - **Active Assist**: Use Recommender API for idle VM/IP detection and rightsizing suggestions.
    - **Review**: Regularly audit "Zombie" resources (unattached disks, unused static IPs, old snapshots).

## Optimization Techniques & Pricing

### Compute

- **Committed Use Discounts (CUDs)**: 1 or 3-year commitment for predictable usage (spend-based or resource-based).
- **Spot VMs**: Up to 91% discount for fault-tolerant, interruptible workloads (batch jobs, GKE nodes).
- **Cloud Run**: Pay only for request processing time (unless using min-instances).

### Data & Storage

- **BigQuery**: Use **Flex Slots** or **Editions** for predictable workloads. Use partition/cluster tables to scan less data.
- **Cloud Storage**: Use **Autoclass** to automatically move objects to the most cost-effective tier.

### Networking

- **Network Pricing**: Understand egress costs. Traffic within a zone is free; inter-zone/inter-region costs money.
- **Cloud CDN**: Cache content at the edge to reduce egress costs and backend load.

## Design Review Checklist

- [ ] Are all resources labeled for cost allocation?
- [ ] Are budgets and alerts configured?
- [ ] Is autoscaling enabled for compute resources?
- [ ] Are CUDs purchased for steady-state baselines?
- [ ] Are Spot VMs used for batch/stateless workloads?
- [ ] Are storage lifecycle policies in place?
