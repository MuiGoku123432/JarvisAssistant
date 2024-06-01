import os
import subprocess

def get_windows_env_variables():
    """Get all Windows system environment variables."""
    env_vars = os.environ
    return env_vars

def set_git_bash_env_variables(env_vars):
    """Set environment variables in Git Bash."""
    for key, value in env_vars.items():
        subprocess.run(['C:\\Program Files\\Git\\bin\\bash.exe', '-c', f'export {key}="{value}"'])

if __name__ == "__main__":
    env_vars = get_windows_env_variables()
    print(env_vars)
    set_git_bash_env_variables(env_vars)
