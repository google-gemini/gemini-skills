# Security, Privacy, and Compliance

[Security](https://cloud.google.com/architecture/framework/security) is a shared responsibility. Google protects the infrastructure; you protect your data and workloads.

## Core Principles

1.  **[Implement Security by Design](https://cloud.google.com/architecture/framework/security/implement-security-by-design)**:
    - **Proactive**: Integrate security early in the design phase (Shift-Left).
    - **Secure Blueprints**: Use [Google Cloud Architecture Center security blueprints](https://cloud.google.com/architecture/security-foundations).
    - **Defense in Depth**: Layer security controls (network, identity, data).

2.  **[Implement Zero Trust (BeyondCorp)](https://cloud.google.com/architecture/framework/security/implement-zero-trust)**:
    - **Verify Explicitly**: Access depends on identity and context, not network location.
    - **Identity-Aware Proxy (IAP)**: Secure access to applications without VPNs.
    - **Least Privilege**: Grant only necessary permissions.

3.  **[Implement Shift-Left Security](https://cloud.google.com/architecture/framework/security/implement-shift-left-security)**:
    - **DevSecOps**: Integrate security scanning (SAST/DAST) into CI/CD pipelines.
    - **Binary Authorization**: Ensure only trusted, signed container images are deployed.
    - **Automated Policy**: Use Organization Policies to enforce guardrails (e.g., restrict public IPs).

4.  **[Implement Preemptive Cyber Defense](https://cloud.google.com/architecture/framework/security/implement-preemptive-cyber-defense)**:
    - **Threat Intelligence**: Use findings to inform defense strategies.
    - **Cloud Armor**: Protect against DDoS and web attacks (WAF).
    - **Security Command Center (SCC)**: Centralized visibility into assets and vulnerabilities.

5.  **[Meet Regulatory and Compliance Needs](https://cloud.google.com/architecture/framework/security/meet-regulatory-compliance-and-privacy-needs)**:
    - **Data Sovereignty**: Control data location using Organization Policies.
    - **Access Transparency**: Monitor Google support access to your data.
    - **Assured Workloads**: Compliance regimes (e.g., FedRAMP, GDPR) made easier.

## Focus Areas & Recommendations

### Identity & Access Management (IAM)

- **Principle of Least Privilege**: Use predefined or custom roles, not Owner/Editor.
- **Service Accounts**: Limit service account privileges and rotate keys.
- **Workforce Identity Federation**: Use to allow external identities (e.g., Azure AD) to access GCP resources without syncing user credentials.

### Data Security

- **Encryption**: Data is encrypted at rest and in transit by default. Use **CMEK** for greater control.
- **Data Loss Prevention (DLP)**: Scan and classify sensitive data (PII, credit cards).

### Network Security

- **VPC Service Controls**: Create security perimeters to prevent data exfiltration.
- **Private Google Access**: Access Google APIs without traversing the public internet.

### AI Security

- **SAIF**: Follow the Secure AI Framework.
- **Protect Models**: Secure AI pipelines and training data from poisoning or theft.
