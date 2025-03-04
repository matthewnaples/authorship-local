import os
import subprocess
import sys
import venv
import re
from pathlib import Path

def run_command(command, shell=True):
    """Run a command and return its output"""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def main():
    # Get the current directory
    current_dir = Path.cwd()
    venv_dir = current_dir / "venv"
    
    # Create virtual environment
    print("Creating virtual environment...")
    venv.create(venv_dir, with_pip=True)
    
    # Determine the path to the Python executable in the virtual environment
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
    else:
        python_path = venv_dir / "bin" / "python"
        activate_script = venv_dir / "bin" / "activate"
    
    # Install requirements
    print("Installing requirements...")
    run_command(f'"{python_path}" -m pip install -r requirements.txt')
    
    # Run chainlit create-secret
    print("Creating Chainlit secret...")
    chainlit_output = run_command(f'"{python_path}" -m chainlit create-secret')
    
    # Extract the secret using regex
    secret_match = re.search(r'CHAINLIT_AUTH_SECRET=["\'](.*)["\']', chainlit_output)
    if not secret_match:
        print("Failed to extract Chainlit secret from output")
        sys.exit(1)
    
    chainlit_secret = secret_match.group(1)
    
    # Create .env file
    print("Creating .env file...")
    env_content = f'''CHAINLIT_AUTH_SECRET="{chainlit_secret}"
OPENAI_API_KEY="fake_key"
'''
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    # Create executable
    print("Creating executable...")
    run_command(f'"{python_path}" -m PyInstaller authorship.spec')
    
    # Print instructions for running the server
    print("\nSetup completed successfully!")
    print("\nTo run the application:")
    print("1. Start the Chainlit server with:")
    if sys.platform == "win32":
        print('    venv\\Scripts\\chainlit run app.py --headless')
    else:
        print('    venv/bin/chainlit run app.py --headless')
    print("2. Once the server is running, you can run the executable from the dist directory")

if __name__ == "__main__":
    main() 