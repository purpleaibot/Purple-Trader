import os
import re

# PROJECT ID: code_rabbit_sentinel_001
# Purpose: Mock "Code Rabbit" / Sentinel security audit.

def run_security_audit():
    findings = []
    
    # Check for hardcoded secrets
    patterns = [r'api_key\s*=\s*["\'][^"\']+["\']', r'secret\s*=\s*["\'][^"\']+["\']']
    
    for root, dirs, files in os.walk("projects/binance-tracker"):
        if "venv" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py") or file.endswith(".env"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            findings.append(f"🚩 Potential Hardcoded Secret in {path}")

    # Check for .env in gitignore
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            if ".env" not in f.read():
                findings.append("🚩 .env not found in .gitignore!")
    
    if not findings:
        return "✅ Code Rabbit Audit: No major security leaks detected. The Sentinel is satisfied."
    else:
        return "❌ Security Findings:\n" + "\n".join(findings)

if __name__ == "__main__":
    print(run_security_audit())
