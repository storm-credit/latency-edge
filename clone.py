import subprocess
import os

repo_url = "https://github.com/storm-credit/claude-skill.git"
target_dir = "claude-skill-repo"

if not os.path.exists(target_dir):
    subprocess.run(["git", "clone", repo_url, target_dir])
    print(f"Cloned {repo_url} to {target_dir}")
else:
    print(f"Directory {target_dir} already exists.")
