# Security Policy

GhostArchive takes security, user privacy, and responsible vulnerability disclosure seriously. Because GhostArchive is a local-first application designed to process personal and sensitive documents, maintaining tight security boundaries is fundamental to the project.

---

## 1. Supported Versions

Only the latest release branch receives security updates and patches.

| Version | Supported |
| :--- | :--- |
| `0.1.x` | :white_check_mark: |
| `< 0.1.0` | :x: |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability in GhostArchive (such as remote code execution, path traversal, injection vulnerability, or unauthorized network leakage), please **do not open a public GitHub issue**.

Instead, report the vulnerability privately:
1. Use GitHub's private security advisory feature under the **Security** tab of the repository (`Report a vulnerability`).
2. Alternatively, email the maintainers directly with details, reproduction steps, and potential impact.

### What to Include in Your Report
- A description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Affected version(s) and operating system environment.
- Any suggested remediation or patch.

### Response Timeline
- **Initial Acknowledgment:** Within 48 hours.
- **Triage & Status Update:** Within 5 business days.
- **Patch & Public Disclosure:** Within 30 days or as mutually coordinated.

---

## 3. Core Security & Privacy Assumptions

GhostArchive is designed with the following security guarantees:
- **Local Loopback Only:** GhostArchive binds by default to `127.0.0.1` and restricts CORS to local Vite origins. It is not designed to be directly exposed to the public internet without an authenticated reverse proxy.
- **No Cloud Document Leakage:** Uploaded documents, chunked text, embeddings, and chat histories reside strictly on the local machine in `backend/data/`.
- **Untrusted Document Framing:** Retrieved document passages are treated strictly as untrusted quoted evidence to mitigate prompt injection attacks.
- **Authoritative Citation Validation:** Model citations are matched against actual retrieved passages; hallucinated chunk IDs are rejected.
