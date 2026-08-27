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

def get_graphql_repo_count(username, token):
    if not token:
        print("❌ Error: GitHub token is required for GraphQL API queries.")
        return

    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Python-Script"
    }
    
    # GraphQL query to get both public and private totals
    query = """
    query($login: String!) {
      user(login: $login) {
        public: repositories(privacy: PUBLIC) {
          totalCount
        }
        private: repositories(privacy: PRIVATE) {
          totalCount
        }
      }
    }
    """
    
    variables = {"login": username}
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    except requests.RequestException as e:
        print(f"❌ Request Error: {e}")
        return
    
    if response.status_code == 200:
        res_data = response.json()
        if "errors" in res_data:
            print(f"❌ GraphQL Error: {res_data['errors']}")
            return
            
        user_data = res_data.get("data", {}).get("user")
        if not user_data:
            print(f"❌ User '{username}' not found.")
            return

        public_count = user_data["public"]["totalCount"]
        private_count = user_data["private"]["totalCount"]
        
        print(f"📊 Public Repositories: {public_count}")
        print(f"🔒 Private Repositories: {private_count}")
        print(f"✨ Total Repositories: {public_count + private_count}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("⚠️ Warning: GITHUB_TOKEN is not set. Please add it to your .env file or export it as an environment variable.")
    get_graphql_repo_count("sindresorhus", token=GITHUB_TOKEN)
