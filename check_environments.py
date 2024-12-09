import subprocess
import sys

# List of required packages
required_packages = [
    'flask',
    'pandas',
    'fuzzywuzzy'
]

# Function to check if a package is installed
def check_and_install(package):
    try:
        __import__(package)
        print(f"Package '{package}' is already installed.")
    except ImportError:
        print(f"Package '{package}' not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check and install missing packages
for package in required_packages:
    check_and_install(package)

print("All necessary packages are installed.")
