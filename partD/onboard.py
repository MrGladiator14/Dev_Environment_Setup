"""
onboard.py: Advanced developer environment verification script.
Features: Dependency fixing, disk space checks, and execution timing.
"""

import sys
import os
import subprocess
import shutil
import time
import argparse
import requests

REQUIRED_PACKAGES = ["pylint", "black", "numpy", "requests"]
TEST_URL = "https://restcountries.com/v3.1/all?fields=name"
REPORT_FILE = "setup_report.txt"
MIN_DISK_GB = 1


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Onboarding Environment Check")
    parser.add_argument("--verbose", action="store_true", help="Show detailed info")
    parser.add_argument("--fix", action="store_true", help="Install missing packages")
    return parser.parse_args()


def timer_decorator(func):
    """Decorator to measure execution time of functions."""

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        duration = end - start
        # result is (status, message, extra_info)
        return (*result, duration)

    return wrapper


@timer_decorator
def check_python():
    """Verify Python version >= 3.10."""
    ver = sys.version_info
    v_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    status = ver.major == 3 and ver.minor >= 10
    msg = f"Python version: {v_str}"
    return status, msg, f"Executable: {sys.executable}"


@timer_decorator
def check_venv():
    """Verify if a virtual environment is active."""
    is_venv = sys.prefix != sys.base_prefix or os.getenv("VIRTUAL_ENV")
    msg = "Virtual environment: Active" if is_venv else "Virtual environment: Missing"
    return is_venv, msg, f"Prefix: {sys.prefix}"


@timer_decorator
def check_dependencies(fix=False):
    """Check and optionally install required packages."""
    missing = []
    found = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            found.append(pkg)
        except ImportError:
            missing.append(pkg)

    if missing and fix:
        print(f"  [FIX] Installing: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        return True, "Dependencies: Fixed/Installed", f"Installed: {missing}"

    status = len(missing) == 0
    msg = "Dependencies: OK" if status else f"Missing: {', '.join(missing)}"
    return status, msg, f"Found: {found}"


@timer_decorator
def check_connectivity():
    """Test internet connectivity."""
    try:
        resp = requests.get(TEST_URL, timeout=5)
        status = resp.status_code == 200
        return status, "Internet connectivity: OK", f"Status Code: {resp.status_code}"
    except requests.RequestException as err:
        return False, "Internet connectivity: Failed", str(err)


@timer_decorator
def check_disk():
    """Check if free disk space is > 1GB."""
    usage = shutil.disk_usage(".")
    free_gb = usage.free / (1024**3)
    status = free_gb >= MIN_DISK_GB
    msg = f"Disk Space: {free_gb:.2f}GB available"
    return status, msg, f"Total: {usage.total / (1024**3):.2f}GB"


def main():
    """Main execution flow."""
    args = get_args()
    start_total = time.perf_counter()
    results = []

    # Run checks
    results.append(check_python())
    results.append(check_venv())
    results.append(check_disk())
    results.append(check_connectivity())
    results.append(check_dependencies(fix=args.fix))

    # File Reporting
    with open(REPORT_FILE, "w", encoding="utf-8") as report, open(
        "requirements.txt", "w", encoding="utf-8"
    ) as reqs:
        # Generate requirements.txt
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=reqs, check=True)

        report.write("ENVIRONMENT CHECK REPORT\n" + "=" * 30 + "\n")
        passed_count = 0

        for status, msg, extra, duration in results:
            prefix = "[PASS]" if status else "[FAIL]"
            if "Disk" in msg and not status:
                prefix = "[WARN]"

            output = f"{prefix} {msg} ({duration:.2f}s)"
            print(output)
            report.write(f"{output}\n")
            if args.verbose:
                print(f"      > {extra}")
                report.write(f"      > {extra}\n")

            if status:
                passed_count += 1

        total_time = time.perf_counter() - start_total
        summary = f"\nTotal execution time: {total_time:.2f}s | Report: {REPORT_FILE}"
        print(f"Result: {passed_count}/{len(results)} checks passed")
        print(summary)
        report.write(summary)


if __name__ == "__main__":
    main()
