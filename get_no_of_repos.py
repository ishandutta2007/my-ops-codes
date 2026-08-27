import csv
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
INPUT_FILE = Path(__file__).resolve().parent / "users.txt"
OUTPUT_FILE = Path(__file__).resolve().parent / "repo_counts.csv"


def get_graphql_repo_count(username, token):
    if not token:
        print(f"❌ Error: GitHub token is required for GraphQL API queries.")
        return None

    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "Python-Script"}

    # GraphQL query to get public (sources & forks) and private totals
    query = """
    query($login: String!) {
      user(login: $login) {
        publicSources: repositories(privacy: PUBLIC, isFork: false) {
          totalCount
        }
        publicForks: repositories(privacy: PUBLIC, isFork: true) {
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
        response = requests.post(
            url, json={"query": query, "variables": variables}, headers=headers
        )
    except requests.RequestException as e:
        print(f"❌ Request Error for {username}: {e}")
        return None

    if response.status_code == 200:
        res_data = response.json()
        if "errors" in res_data:
            print(f"❌ GraphQL Error for {username}: {res_data['errors']}")
            return None

        user_data = res_data.get("data", {}).get("user")
        if not user_data:
            print(f"❌ User '{username}' not found.")
            return None

        public_sources = user_data["publicSources"]["totalCount"]
        public_forks = user_data["publicForks"]["totalCount"]
        public_count = public_sources + public_forks
        private_count = user_data["private"]["totalCount"]
        total_count = public_count + private_count

        print(f"\n👤 User: {username}")
        print(f"📊 Public Repositories: {public_count}")
        print(f"   ├─ 📦 Sources (Own/Original): {public_sources}")
        print(f"   └─ 🍴 Forks: {public_forks}")
        print(f"🔒 Private Repositories: {private_count}")
        print(f"✨ Total Repositories: {total_count}")

        return {
            "username": username,
            "public_repositories": public_count,
            "public_sources": public_sources,
            "public_forks": public_forks,
            "private_repositories": private_count,
            "total_repositories": total_count,
        }
    else:
        print(f"❌ Error fetching {username}: {response.status_code} - {response.text}")
        return None


def read_users_from_file(file_path):
    """Read a list of usernames from a file, ignoring empty lines and comments."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Input file '{file_path}' does not exist.")
        return []

    users = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            username = line.strip()
            if username and not username.startswith("#"):
                users.append(username)
    return users


def save_results_to_csv(results, file_path):
    """Save user repository counts to a CSV file."""
    fieldnames = [
        "Username",
        "Public Repositories",
        "Public Sources",
        "Public Forks",
        "Private Repositories",
        "Total Repositories",
    ]
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "Username": r["username"],
                    "Public Repositories": r["public_repositories"],
                    "Public Sources": r["public_sources"],
                    "Public Forks": r["public_forks"],
                    "Private Repositories": r["private_repositories"],
                    "Total Repositories": r["total_repositories"],
                }
            )
    print(f"\n📁 Saved results to '{file_path}'")


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print(
            "⚠️ Warning: GITHUB_TOKEN is not set. Please add it to your .env file or export it as an environment variable."
        )

    users = read_users_from_file(INPUT_FILE)
    if not users:
        print(
            f"No usernames found in '{INPUT_FILE}'. Please add at least one username per line."
        )
    else:
        print(f"Found {len(users)} user(s) to process from '{INPUT_FILE}'.")
        results = []
        for username in users:
            data = get_graphql_repo_count(username, token=GITHUB_TOKEN)
            if data:
                results.append(data)

        if results:
            save_results_to_csv(results, OUTPUT_FILE)
