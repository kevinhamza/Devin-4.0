# Devin AI Prompt Engineering Guide

Effective interaction with powerful AI like Devin often depends on crafting clear, specific, and well-structured prompts. This guide collects examples and tips shared by the community to help users get the most out of Devin for various tasks.

**Contribute:** Please add your successful prompts and techniques! Edit this file and submit a pull request or share in the community channels.

---

## General Prompting Principles

* **Be Specific and Clear:** Avoid ambiguity. State exactly what you want the AI to do, the context, and the desired output format.
* **Provide Context:** Give the AI relevant background information. For ongoing tasks, refer to previous steps or findings. If working with files or code, provide the relevant snippets or paths.
* **Define the Role/Persona (Optional):** Sometimes helpful to tell the AI what role to adopt (e.g., "Act as an expert penetration tester," "Act as a helpful Python code reviewer").
* **Specify the Output Format:** Ask for output in a specific format if needed (e.g., "Provide the output as a JSON list," "Write the report section in Markdown," "List the steps numerically").
* **Ask for Reasoning (Chain-of-Thought):** For complex tasks, ask Devin to "think step-by-step" or "explain its reasoning" before providing the final answer or taking action. This helps verify the logic and can lead to better results.
* **Break Down Complex Tasks:** Instead of one massive prompt, consider breaking complex goals into smaller, sequential prompts or sub-tasks.
* **Iterate and Refine:** Don't expect the first prompt to be perfect. Analyze the AI's response and refine your prompt based on the output if it's not quite right. Add constraints or clarify instructions.

---

## Task-Specific Prompt Examples

### Security Scanning & Analysis

* **Generating Scan Commands:**
    > "Generate an Nmap command to perform a TCP SYN scan (`-sS`) on the 1000 most common ports, detect service versions (`-sV`), run default safe scripts (`-sC`), use aggressive timing (`-T4`), and save all output formats (`-oA`) to a file named `nmap_scan_results` for the target IP address `192.168.1.101`."

* **Analyzing Scan Results:**
    > "Analyze the attached Nmap XML output file (`/path/to/nmap_scan.xml`). Provide a summary of findings including:
    > 1.  A list of all open ports with their associated services and versions.
    > 2.  Any potential high or critical severity vulnerabilities identified by Nmap scripts.
    > 3.  Suggest the top 3 most promising services/ports to investigate further for initial access."

* **Interpreting Tool Output (Generic):**
    > "Interpret the following output from the `enum4linux` tool run against `10.0.0.5`. Focus on identifying potential usernames, shares, and domain information relevant for enumeration."
    > ```
    > [Paste enum4linux output here]
    > ```

* **Suggesting Exploits (Use with Caution & Ethics):**
    > "Given the following service identified on `10.0.0.20:21`: `vsftpd 2.3.4`. What known public exploits (e.g., Metasploit modules, Exploit-DB references) exist for this specific version? Prioritize exploits that might grant remote code execution."

### Code Generation & Debugging

* **Writing a Function:**
    > "Write a Python function named `upload_file_to_s3` that takes `bucket_name`, `object_key`, and `file_path` as arguments. It should use the `boto3` library to upload the file. Include basic error handling for `ClientError` and `NoCredentialsError`, logging appropriate messages. Include type hints and a docstring explaining its purpose and arguments."

* **Generating Boilerplate:**
    > "Generate a basic FastAPI application structure in Python. Include:
    > 1.  A main `app` instance.
    > 2.  A root endpoint (`/`) returning `{\"message\": \"Hello World\"}`.
    > 3.  A health check endpoint (`/health`) returning `{\"status\": \"OK\"}`.
    > 4.  Include necessary imports and basic Uvicorn run block for `if __name__ == '__main__':`."

* **Debugging Code:**
    > "Debug the following Python code snippet. Identify the cause of the `IndexError` and suggest a fix. Explain the reasoning."
    > ```python
    > my_list = [1, 2, 3]
    > for i in range(4):
    >   print(my_list[i] * 2)
    > ```

* **Refactoring Code:**
    > "Refactor this Python code to be more efficient and follow PEP 8 guidelines. Explain the changes made."
    > ```python
    > # [Paste less efficient / poorly formatted code here]
    > ```

### Automation & System Tasks

* **File Management:**
    > "Search the directory `/home/user/documents` and all its subdirectories for PDF files modified in the last 7 days. Move the found files to `/home/user/recent_pdfs`. Log the names of moved files to `/home/user/logs/move_log.txt`."

* **Running Terminal Commands:**
    > "Execute the following shell command and return its standard output: `df -h /`"
    > **Note:** Ensure Devin has appropriate permissions and sandboxing if executing arbitrary commands!

* **Process Monitoring:**
    > "Check if a process named `nginx` is running on the system. If it is, return its PID. If not, return 'Not running'."

### Information Retrieval & Reporting

* **Summarizing Text:**
    > "Summarize the key findings and recommendations from the attached penetration test report (`/path/to/pentest_report.pdf`). Focus on critical and high severity vulnerabilities. Provide the summary as bullet points."

* **Extracting Information:**
    * > "Extract all IP addresses and CVE identifiers mentioned in the following text:"
        > ```
        > [Paste log file snippet or report text here]
        > ```

* **Generating Report Sections:**
    > "Write a vulnerability description for a finding titled 'Reflected Cross-Site Scripting (XSS) in Search Parameter'. Include:
    > 1.  A brief explanation of XSS.
    > 2.  How the vulnerability was identified on the `/search` page via the `q` parameter.
    > 3.  A proof-of-concept URL.
    > 4.  An assessment of the impact (e.g., session hijacking).
    > 5.  A recommendation for remediation (e.g., context-aware output encoding)."

---

Remember to adapt these examples to your specific needs and the capabilities of the AI model you are interacting with. Clear, contextual prompts yield better results!
