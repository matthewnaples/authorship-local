import os
import subprocess
import sys
import venv
import re
import argparse
from pathlib import Path
from enum import Enum, auto

class SetupStep(Enum):
    CREATE_VENV = auto()
    INSTALL_REQUIREMENTS = auto()
    CREATE_CHAINLIT_SECRET = auto()
    CREATE_ENV_FILE = auto()
    CREATE_EXECUTABLE = auto()
    ALL = auto()

def run_command(command, shell=True):
    """Run a command and return its output"""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

class Setup:
    def __init__(self):
        self.current_dir = Path.cwd()
        self.venv_dir = self.current_dir / "venv"
        
        # Set platform-specific paths
        if sys.platform == "win32":
            self.python_path = self.venv_dir / "Scripts" / "python.exe"
            self.activate_script = self.venv_dir / "Scripts" / "activate.bat"
            self.chainlit_path = self.venv_dir / "Scripts" / "chainlit"
        else:
            self.python_path = self.venv_dir / "bin" / "python"
            self.activate_script = self.venv_dir / "bin" / "activate"
            self.chainlit_path = self.venv_dir / "bin" / "chainlit"

    def create_venv(self):
        """Step 1: Create virtual environment"""
        print("Creating virtual environment...")
        venv.create(self.venv_dir, with_pip=True)

    def install_requirements(self):
        """Step 2: Install requirements"""
        print("Installing requirements...")
        run_command(f'"{self.python_path}" -m pip install -r requirements.txt')

    def create_chainlit_secret(self):
        """Step 3: Create Chainlit secret"""
        print("Creating Chainlit secret...")
        chainlit_output = run_command(f'"{self.python_path}" -m chainlit create-secret')
        
        secret_match = re.search(r'CHAINLIT_AUTH_SECRET=["\'](.*)["\']', chainlit_output)
        if not secret_match:
            print("Failed to extract Chainlit secret from output")
            sys.exit(1)
        
        return secret_match.group(1)

    def create_env_file(self, chainlit_secret):
        """Step 4: Create .env file"""
        print("Creating .env file...")
        env_content = f'''CHAINLIT_AUTH_SECRET="{chainlit_secret}"
OPENAI_API_KEY="fake_key"
'''
        with open(".env", "w") as f:
            f.write(env_content)

    def create_executable(self):
        """Step 5: Create executable"""
        print("Creating executable...")
        run_command(f'"{self.python_path}" -m PyInstaller authorship.spec')

    def print_final_instructions(self):
        """Print instructions for running the server"""
        print("\nSetup completed successfully!")
        print("\nTo run the application:")
        print("1. Start the Chainlit server with:")
        if sys.platform == "win32":
            print('    venv\\Scripts\\chainlit run app.py --headless')
        else:
            print('    venv/bin/chainlit run app.py --headless')
        print("2. Once the server is running, you can run the executable from the dist directory")

def parse_args():
    parser = argparse.ArgumentParser(
        description='Setup script for Authorship Local',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Run all steps (default):
    python setup.py
    python setup.py --start-step all

  Start from a specific step:
    python setup.py --start-step install_requirements
    python setup.py --start-step create_chainlit_secret

Available steps (in order):
  - create_venv
  - install_requirements
  - create_chainlit_secret
  - create_env_file
  - create_executable
  - all (default)
''')
    parser.add_argument(
        '--start-step',
        type=str,
        choices=[step.name.lower() for step in SetupStep],
        help='Start setup from a specific step (default: all)',
        default='all',
        metavar='STEP'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    setup = Setup()
    
    # Map steps to their corresponding functions
    steps = {
        SetupStep.CREATE_VENV: setup.create_venv,
        SetupStep.INSTALL_REQUIREMENTS: setup.install_requirements,
        SetupStep.CREATE_CHAINLIT_SECRET: setup.create_chainlit_secret,
        SetupStep.CREATE_ENV_FILE: lambda: setup.create_env_file(setup.create_chainlit_secret()),
        SetupStep.CREATE_EXECUTABLE: setup.create_executable,
    }
    
    # Determine which steps to run
    start_step = SetupStep[args.start_step.upper()]
    should_run = False
    chainlit_secret = None
    
    for step in SetupStep:
        if step == SetupStep.ALL:
            continue
            
        if step == start_step or start_step == SetupStep.ALL:
            should_run = True
            
        if should_run:
            if step == SetupStep.CREATE_ENV_FILE and chainlit_secret is None:
                chainlit_secret = setup.create_chainlit_secret()
                setup.create_env_file(chainlit_secret)
            else:
                result = steps[step]()
                if step == SetupStep.CREATE_CHAINLIT_SECRET:
                    chainlit_secret = result
    
    setup.print_final_instructions()

if __name__ == "__main__":
    main() 