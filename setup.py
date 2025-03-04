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

def run_command(command, shell=True, show_output=False, activate_venv=False):
    """Run a command and return its output
    
    Args:
        command: The command to run
        shell: Whether to run the command in a shell
        show_output: Whether to show real-time output in the terminal
        activate_venv: Whether to run the command with activated virtual environment
    """
    try:
        if activate_venv:
            # Construct the activation command based on the platform
            if sys.platform == "win32":
                activate_cmd = f'"{Path.cwd() / "venv" / "Scripts" / "activate.bat"}" && '
            else:
                activate_cmd = f'source "{Path.cwd() / "venv" / "bin" / "activate"}" && '
            command = activate_cmd + command

        if show_output:
            # Run with output displayed in real-time
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            for line in process.stdout:
                print(line, end='')  # Print in real-time
                output_lines.append(line)
            
            process.wait()
            if process.returncode != 0:
                print(f"Error: Command '{command}' failed with return code {process.returncode}")
                sys.exit(1)
            
            return ''.join(output_lines)
        else:
            # Run with captured output
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
        run_command(f'"{self.python_path}" -m pip install -r requirements.txt', show_output=True)

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
        try:
            # Ensure the dist directory exists and is empty
            dist_dir = self.current_dir / "dist"
            if dist_dir.exists():
                print("Cleaning dist directory...")
                for item in dist_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
            else:
                dist_dir.mkdir(parents=True)

            # Ensure the build directory is clean
            build_dir = self.current_dir / "build"
            if build_dir.exists():
                print("Cleaning build directory...")
                import shutil
                shutil.rmtree(build_dir)

            # Run PyInstaller with absolute paths and activated virtual environment
            spec_file = self.current_dir / "authorship.spec"
            if not spec_file.exists():
                print(f"Error: Could not find spec file at {spec_file}")
                sys.exit(1)

            print("Running PyInstaller with activated virtual environment...")
            command = f'pyinstaller "{spec_file}" --clean'
            run_command(command, show_output=True, activate_venv=True)

            # Verify the executable was created
            if sys.platform == "win32":
                exe_path = dist_dir / "Authorship.exe"
            else:
                exe_path = dist_dir / "Authorship"

            if not exe_path.exists():
                print(f"Error: Executable was not created at expected path: {exe_path}")
                sys.exit(1)

            print(f"Successfully created executable at: {exe_path}")

        except Exception as e:
            print(f"Error creating executable: {str(e)}")
            sys.exit(1)

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