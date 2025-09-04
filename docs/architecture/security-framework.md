# Security Framework Architecture

## Overview

The Autocoder system is **secure by default**. The architecture mandates a multi-layered security approach that provides defense-in-depth, covering the supply chain, the generation pipeline, and the runtime environment. These controls are not optional; they are enforced by the build pipeline, and any failure is a build-stopping event.

---

## Pillar 1: Supply Chain Security (SLSA-2 Compliance)

The architecture requires a secure supply chain to guarantee the integrity of the generated code. This is non-negotiable.

*   **Dependency Locking (`build.lock`):** All dependencies are pinned in a lockfile to prevent resolution attacks.
*   **Provenance Signing (`cosign`):** The build process **must** generate a Sigstore signature for the `build.lock` to prove its provenance. CI/CD pipelines **must** be configured to verify this signature before deployment.
*   **AST Secret Scanning:** The CI pipeline includes a static analysis step that scans for hard-coded secrets. The build fails if any are found.

*> **Note on SLSA-2 Compliance:** These measures provide a strong foundation for supply-chain security. Achieving full SLSA-2 compliance also requires bit-for-bit reproducible builds, which is a planned future work item dependent on a standardized build toolchain (e.g., Bazel).*

---

## Pillar 2: Generation-Time Security

Security controls are embedded directly into the code generation and validation pipeline and are strictly enforced.

*   **Policy-as-Code Enforcement:** The `architecture.yaml` includes a `policy` block for defining security constraints (e.g., `require_https`). These policies are not advisory; they are strictly enforced by the validation framework, and violations will fail the build.
*   **AST Security Validator:** The validation stage includes a set of rules that scan the generated code's Abstract Syntax Tree (AST) for dangerous patterns (e.g., use of `os.system`, SQL injection vulnerabilities). The build will fail if any unsafe patterns are detected.

---

## Pillar 3: Runtime Security

The generated system runtime is hardened and secure by default. Security features are opt-out, not opt-in, and disabling them requires an explicit, audited `unsafe_allow_insecure_runtime` flag in the `deployment.yaml` along with a risk-acceptance ticket.

### Authentication & Authorization

*   **JWT-Based Authentication with Pluggable Cryptographic Policy:**
    *   **Cryptographic Policy Configuration:** The system uses `config/cryptographic_policy.yaml` to define environment-specific JWT algorithm policies. This ensures appropriate security levels for each deployment environment.
    *   **Environment-Specific Algorithms:**
        *   **Development:** Allows `HS256` for simplicity (with deprecation warnings)
        *   **Testing:** Prefers `RS256` but allows `HS256` for test automation
        *   **Staging:** Only allows `RS256` and `ES256` (production-like security)
        *   **Production:** Enforces `RS256` or `ES256` only, with enhanced key management
    *   **Algorithm Support:**
        *   **HS256:** Symmetric signing with HMAC-SHA256 (development only)
        *   **RS256:** Asymmetric signing with RSA-SHA256 and JWKS distribution
        *   **ES256:** Asymmetric signing with ECDSA-P256 (future enhancement)
    *   **Policy Enforcement:** CI/CD pipeline validates that deployment configurations comply with the cryptographic policy. Policy violations cause build failures.
    *   **Migration Strategy:**
        1.  Cryptographic policy is enforced at build time through validation framework
        2.  Development environments receive deprecation warnings for HS256 usage
        3.  Production environments strictly enforce RS256/ES256 with vault-based key storage
        4.  Automatic policy compliance reporting and monitoring

*> **Note on JWKS Rotation:** Any compliant runtime implementation **must** include a strategy to mitigate potential cache-coherency issues during key rotation (e.g., via sidecar-based hot-reloading or a centralized discovery service).*

### Input Sanitization

*   **Mandatory Input Sanitization:** All user-provided input **must** be sanitized to prevent injection attacks. This is enforced by the AST validator, which checks for the correct usage of vetted libraries for SQL, HTML, and other content types.

### Path Traversal

*   **Mandatory Path Validation:** All file system access **must** be validated to prevent path traversal attacks. Component logic must resolve all paths against a secure, defined base directory. This is enforced by the AST validator.

### Secrets Management

*   **Production-Grade Secrets Management:** The architecture requires integration with a production-grade secrets management system like HashiCorp Vault or Kubernetes Sealed Secrets. Secrets **must not** be stored in environment variables in production deployments, as defined by the `deployment.yaml` for that environment.

### Secure Command Execution

*   **Forbidden Direct Execution:** Any execution of shell commands **must** be done through a sanitized, validated interface. Direct use of `subprocess.Popen(shell=True)` or `os.system` is forbidden by the AST validator and will fail the build. 