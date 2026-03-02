"""
onboard.py: A script to verify developer environments.
Checks Python version, venv status, dependencies, and connectivity.
"""

import sys
import os
import subprocess
import platform
import requests

REQUIRED_PACKAGES = ["pylint", "black", "numpy", "requests"]
TEST_URL = "https://restcountries.com/v3.1/all?fields=name"
REPORT_FILE = "setup_report.txt"


def check_python_version():
    """Verify Python version is >= 3.10."""
    major, minor = sys.version_info.major, sys.version_info.minor
    version_str = f"{major}.{minor}.{sys.version_info.micro}"
    if major == 3 and minor >= 10:
        return True, f"Python version: {version_str}"
    return False, f"Python version: {version_str} (Warning: < 3.10)"


def check_virtual_env():
    """Check if a virtual environment is active."""
    # Checks for PEP 405 compliance or typical env markers
    in_venv = (
        hasattr(sys, "real_prefix")
        or (sys.base_prefix != sys.prefix)
        or os.getenv("VIRTUAL_ENV")
    )
    if in_venv:
        return True, "Virtual environment: Active"
    return False, "Virtual environment: Missing"


def check_dependencies():
    """Check for required packages and retrieve their versions."""
    results = []
    missing = []
    installed_versions = []

    for package in REQUIRED_PACKAGES:
        try:
            # Using subprocess to get version to ensure we check the environment
            version = subprocess.check_output(
                [sys.executable, "-m", "pip", "show", package],
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in version.splitlines():
                if line.startswith("Version:"):
                    ver_num = line.split(": ")[1]
                    installed_versions.append(f"{package}=={ver_num}")
                    break
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(package)

    if not missing:
        return True, "pylint/black/numpy/requests: Installed", installed_versions
    return False, f"Missing packages: {', '.join(missing)}", installed_versions


def check_connectivity():
    """Test internet connectivity via restcountries API."""
    try:
        response = requests.get(TEST_URL, timeout=5)
        if response.status_code == 200:
            return True, "Internet connectivity: OK"
        return False, f"Connectivity: HTTP {response.status_code}"
    except requests.RequestException:
        return False, "Internet connectivity: Failed"


def generate_requirements():
    """Generate a requirements.txt based on current environment."""
    try:
        data = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        with open("requirements.txt", "wb") as req_file:
            req_file.write(data)
        return True
    except subprocess.SubprocessError:
        return False


def main():
    """Orchestrate all environment checks."""
    checks = []
    report_lines = [f"Environment Report - {platform.system()}\n", "=" * 30 + "\n"]

    # Run Checks
    py_pass, py_msg = check_python_version()
    venv_pass, venv_msg = check_virtual_env()
    dep_pass, dep_msg, dep_list = check_dependencies()
    conn_pass, conn_msg = check_connectivity()

    results = [
        ("[PASS]" if py_pass else "[WARN]", py_msg, py_pass),
        ("[PASS]" if venv_pass else "[FAIL]", venv_msg, venv_pass),
        ("[PASS]" if dep_pass else "[FAIL]", dep_msg, dep_pass),
        ("[PASS]" if conn_pass else "[FAIL]", conn_msg, conn_pass),
    ]

    # Console Output & Report Assembly
    passed_count = sum(1 for _, _, success in results if success)
    for prefix, msg, _ in results:
        print(f"{prefix} {msg}")
        report_lines.append(f"{prefix} {msg}\n")

    if dep_list:
        report_lines.append("\nInstalled Versions:\n" + "\n".join(dep_list) + "\n")

    # Final logic
    generate_requirements()
    summary = f"\nResult: {passed_count}/{len(results)} checks passed"
    print(f"{summary} | Report: {REPORT_FILE}")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
        f.write(summary)


if __name__ == "__main__":
    main()