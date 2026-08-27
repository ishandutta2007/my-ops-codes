import json
import os
from pathlib import Path
import requests

def load_env(env_path=None):
    """Load environment variables from a .env file into os.environ."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent / ".env"
    else:
        env_path = Path(env_path)

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val

# Load .env file
load_env()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

# Headers required for GitHub API
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_all_repositories():
    repos = []
    page = 1
    per_page = 100
    
    print("Fetching repositories from GitHub...")
    
    while True:
        # Use /user/repos to get both public and private repositories across owned and collab accounts
        # Append &type=owner if you ONLY want repositories owned by you
        url = f"https://api.github.com/user/repos?per_page={per_page}&page={page}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        
        # If the page is empty, we have reached the end
        if not data:
            break
            
        repos.extend(data)
        print(f"Retrieved page {page} ({len(data)} repositories found)")
        page += 1
        
    return repos

def save_to_files(repos):
    # 1. Save full JSON metadata
    json_filename = "github_repos_detailed.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=4)
    print(f"Saved complete metadata to '{json_filename}'")
    
    # 2. Save a clean, readable text list of URLs
    txt_filename = "github_repos_list.txt"
    with open(txt_filename, "w", encoding="utf-8") as f:
        for repo in repos:
            # You can change this to repo['name'] or repo['full_name'] depending on preference
            f.write(f"{repo['html_url']}\n")
    print(f"Saved clean repository list to '{txt_filename}'")

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN is not set. Please add it to your .env file or export it as an environment variable.")
    else:
        all_repos = get_all_repositories()
        if all_repos:
            print(f"\nSuccessfully fetched {len(all_repos)} repositories in total.")
            save_to_files(all_repos)
