# Guide to Security Threat Modeling

This document provides a methodology and a reusable template for conducting a security threat modeling exercise. This process is designed to be performed early in the software development lifecycle (SDLC) to proactively identify and mitigate security risks.

---

## 1. What is Threat Modeling?

Threat modeling is a structured, proactive process for identifying, evaluating, and mitigating potential security threats to a system. It is a form of risk assessment that is about thinking like an attacker *before* an application is built or deployed. The goal is to build more secure applications from the ground up by answering three fundamental questions:

1.  **What are we building?** (Application Decomposition)
2.  **What can go wrong?** (Threat Identification & Rating)
3.  **What are we going to do about it?** (Mitigation Planning)

---

## 2. Methodology: STRIDE

We will use the **STRIDE** methodology, developed by Microsoft, to systematically categorize and brainstorm potential threats. STRIDE is a mnemonic for the following six threat categories:

-   **S**poofing: Illegitimately assuming the identity of another user, component, or entity. *Example: An attacker uses a stolen session cookie to impersonate a legitimate user.*
-   **T**ampering: Unauthorized modification of data, either in transit (e.g., man-in-the-middle attack) or at rest (e.g., SQL injection).
-   **R**epudiation: The inability to prove that an action was performed by a specific user or entity. *Example: The application has no audit logs, so an administrator can delete records and deny having done so.*
-   **I**nformation Disclosure: The exposure of sensitive information to unauthorized individuals. *Example: A directory listing on the web server exposes internal file names.*
-   **D**enial of Service (DoS): Making a system or resource unavailable to legitimate users. *Example: An attacker floods the login endpoint with requests, locking out all user accounts.*
-   **E**levation of Privilege: Gaining capabilities or permissions beyond what is authorized. *Example: A regular user finds a way to access an administrative API endpoint.*

---

## 3. The Threat Modeling Process

### Step 1: Decompose the Application
Before you can find threats, you must understand the system. The best way to do this is by creating a **Data Flow Diagram (DFD)**. A DFD should visualize the following components:

-   **Processes**: Components that handle or transform data (e.g., a web server, an API backend, a microservice).
-   **Data Stores**: Where data is stored at rest (e.g., a SQL database, a file system, a cache).
-   **External Entities**: Users, actors, or external systems that interact with your application.
-   **Data Flows**: The arrows that show how data moves between the other elements.
-   **Trust Boundaries**: Dotted lines that separate zones with different levels of trust (e.g., the boundary between the public internet and your internal network).

### Step 2: Identify Threats
For every element in your DFD, systematically apply the STRIDE model to brainstorm potential threats. Ask questions like: "How could an attacker **S**poof this user?", "How could they **T**amper with this data flow?", "How could they cause a **D**enial of Service against this process?".

### Step 3: Rate and Prioritize Threats
Once you have a list of threats, you need to prioritize them. A simple **High/Medium/Low** rating based on **Likelihood** and **Impact** is an effective starting point.

-   **Likelihood:** How probable is it that this threat could be exploited? (Consider skill required, discoverability, etc.)
-   **Impact:** What would the business impact be if this threat were realized? (Consider financial loss, reputational damage, data loss, etc.)

### Step 4: Mitigate Threats
For each threat (especially High and Medium priority ones), define a concrete mitigation or countermeasure. This is the plan for "what to do about it." Mitigations can be a technology, a code change, or a process change.

---

## 4. Threat Model Template

*Copy and use the section below for your own threat modeling exercise.*

### **Project:** `[PROJECT_NAME]`

-   **Version:** `[VERSION]`
-   **Date:** `[YYYY-MM-DD]`

#### **A. Application Decomposition**

**Description:**
> [A brief, high-level description of the application's purpose and architecture.]

**Data Flow Diagram (DFD):**
> `![DFD Image](path/to/dfd.png)`
> *(If an image isn't available, describe the key components, data flows, and trust boundaries in a list).*

#### **B. Threat Analysis and Mitigation Table**

| ID | DFD Element | Threat (STRIDE Category) | Description of Threat | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation Strategy | Status |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T001** | *[e.g., User Authentication Flow]* | **S**poofing | *An attacker could steal a user's non-expiring session cookie to impersonate them indefinitely.* | M | H | *Implement secure cookie flags (HttpOnly, Secure) and enforce a short, sliding session timeout.* | *[Not Started / Mitigated / Accepted]* |
| **T002** | *[e.g., User Profile Database]* | **I**nformation Disclosure | *The database stores user passwords in plain text. A database breach would expose all user credentials.* | H | H | *Hash all user passwords using a modern, salted, and peppered hashing algorithm like Argon2id or bcrypt.* | *[Not Started / Mitigated / Accepted]* |
| **T003** | *[e.g., Admin API Endpoint]* | **E**levation of Privilege | *The API endpoint `/api/admin/deleteUser` does not properly verify that the calling user has administrative privileges.* | M | H | *Implement role-based access control (RBAC) checks on all sensitive API endpoints.* | *[Not Started / Mitigated / Accepted]* |
| **T004**| | | | | | | |
