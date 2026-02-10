---
name: google-cloud-architect
description: Designs, reviews, and optimizes Google Cloud architectures using the Google Cloud Architecture Framework. Use for designing new solutions, auditing existing workloads, or seeking best practices (Security, Reliability, Cost, etc.).
---

# Google Cloud Architect Skill

## Overview

This skill provides expert guidance on designing scalable, resilient, and secure solutions on Google Cloud Platform (GCP), strictly adhering to the **[Google Cloud Architecture Framework](https://cloud.google.com/architecture/framework)** and best practices from the **[Google Cloud Architecture Center](https://cloud.google.com/architecture)**.

## Architecture Framework Pillars

### 1. Operational Excellence

Efficiently deploy, operate, monitor, and manage cloud workloads.

- **Key Practices:** Automate deployments (CI/CD), implement comprehensive observability (Monitoring/Logging), and establish incident management processes.
- **Detailed Guidance:** See [references/operational-excellence.md](references/operational-excellence.md).

### 2. Security, Privacy, and Compliance

Protect data and workloads while meeting regulatory requirements.

- **Key Practices:** Implement "Shared Responsibility" model, Zero Trust security (BeyondCorp), least privilege IAM, and data encryption (CMEK/KMS).
- **Detailed Guidance:** See [references/security.md](references/security.md).

### 3. Reliability

Design and operate resilient and highly available workloads.

- **Key Practices:** Design for failure, implement multi-region/zone redundancy, establish SLOs/SLIs, and automate disaster recovery.
- **Detailed Guidance:** See [references/reliability.md](references/reliability.md).

### 4. Cost Optimization

Maximize the business value of your Google Cloud investment.

- **Key Practices:** Use FinOps practices, right-size resources, leverage committed use discounts (CUDs), and use Spot VMs for interruptible tasks.
- **Detailed Guidance:** See [references/cost-optimization.md](references/cost-optimization.md).

### 5. Performance Optimization

Design and tune resources for optimal performance.

- **Key Practices:** Select appropriate compute/storage classes, implement caching (Cloud CDN, Memorystore), and monitor latency and throughput.
- **Detailed Guidance:** See [references/performance-optimization.md](references/performance-optimization.md).

### 6. Sustainability

Build and manage environmentally sustainable cloud workloads.

- **Key Practices:** Choose low-carbon regions, minimize data movement, and optimize resource utilization to reduce carbon footprint.
- **Detailed Guidance:** See [references/sustainability.md](references/sustainability.md).

## Core Design Principles

- **Design for Change:** Architect systems to evolve. Enable frequent, small updates and rapid feedback loops (DORA metrics).
- **Document Your Architecture:** Maintain clear design records and standards to facilitate collaboration and future decisions.
- **Simplify & Use Managed Services:** Prefer PaaS/Serverless (Cloud Run, GKE, BigQuery) to minimize operational overhead.
- **Decouple Architecture:** Use microservices and asynchronous communication (Pub/Sub) to increase flexibility and resilience.
- **Statelessness:** Design applications to be stateless for better scalability and faster recovery.

## Architecture Design Workflow

Follow this process when helping users design or review architectures. Copy the checklist below to track progress.

### Architecture Design Checklist

- [ ] **1. Clarify Requirements**: Ensure the goal, scope, and constraints are clear.
- [ ] **2. Verify Completeness**: Use the [Requirement Assessment](#requirement-assessment) questions to identify gaps.
- [ ] **3. Draft Initial Design**: Propose a high-level architecture based on [Core Design Principles](#core-design-principles).
- [ ] **4. Pillar Review**: Review the design against all 6 [Architecture Framework Pillars](#architecture-framework-pillars).
- [ ] **5. Refine & Finalize**: Adjust based on trade-off analysis and user feedback.

## Requirement Assessment

If the user's request is vague (e.g., "Build me a photo app"), use these questions to clarify requirements **before** designing. **Do not proceed** to design until you have a reasonable understanding of these constraints.

**1. Operational Excellence**

- _Deployment_: "How often do you plan to deploy? Do you need zero-downtime updates?"
- _Team_: "What is the size and skill level of the operations team? (e.g., SRE experience)"
- _Monitoring_: "What are the critical signals that indicate system health?"

**2. Security**

- _Compliance_: "Are there specific regulatory requirements (e.g., GDPR, HIPAA, PCI-DSS)?"
- _Access_: "Is the application internet-facing or internal-only? Who needs access?"
- _Data_: "Do you store PII or other sensitive data? What are the retention requirements?"

**3. Reliability**

- _Criticality_: "What is the business impact of a 1-hour outage?"
- _Availability_: "What is your target availability SLO (e.g., 99.9%, 99.95%, 99.99%)? This will determine whether a zonal, regional, or multi-region architecture is needed."
- _Recovery_: "What is your RPO (max data loss) and RTO (max downtime) in a disaster?"

**4. Cost Optimization**

- _Budget_: "Is there a strict monthly budget? CapEx vs OpEx preference?"
- _Traffic Patterns_: "Is the workload steady, bursty, or predictable?"
- _Lifecycle_: "Is this a temporary POC or a long-running production system?"

**5. Performance**

- _Scale_: "What is the expected number of concurrent users (peak vs. average)?"
- _Latency_: "What is the maximum acceptable latency? (e.g., <100ms for real-time)"
- _Throughput_: "What is the expected requests per second (RPS) or data ingestion rate?"

**6. Sustainability**

- _Targets_: "Does your organization have specific carbon reduction goals?"
- _Scheduling_: "Can batch jobs be deferred to run when energy is cleaner?"
- _Region_: "Are you flexible with region selection to prioritize low-carbon energy?"

## Design Review Checklist

Use these questions to audit an architecture:

- [ ] **Ops:** Is the deployment automated? Is there a rollback strategy?
- [ ] **Security:** Is the principle of least privilege applied? Is data encrypted at rest and in transit?
- [ ] **Reliability:** What happens if a zone fails? RTO/RPO defined?
- [ ] **Cost:** Are there unused resources? Are we using the right machine types?
- [ ] **Performance:** Is caching used effectively? Are database queries optimized?
- [ ] **Sustainability:** Can we use a cleaner region? Can we shut down dev environments at night?

## Trade-off Analysis

Architecture is about balance.

- **Reliability vs. Cost:** High availability (multi-region) costs more.
- **Security vs. Agility:** Strict controls can slow down deployment if not automated.
- **Performance vs. Cost:** Higher performance SKU often means higher price.
  _Always align trade-offs with business requirements._
