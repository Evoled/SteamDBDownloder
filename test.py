import subprocess

# Set your Steam App ID, Depot ID, and branch
APP_ID = "1091500"  # Cyberpunk 2077
DEPOT_ID = "1091501"  # Base game depot
BRANCH = "public"  # Specify branch if necessary

# Steam username and password
USERNAME = "your_steam_username"
PASSWORD = "your_steam_password"


def fetch_manifest(app_id, depot_id, username, password, branch="public"):
    try:
        # Command to run DepotDownloader for fetching the depot manifest
        command = [
            "DepotDownloader.exe",
            "-app", app_id,
            "-depot", depot_id,
            "-manifest-only",
            "-username", username,
            "-password", password,
            "-beta", branch
        ]

        # Run the command
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check output for errors or successful result
        if result.returncode == 0:
            print(f"Manifest fetched successfully for App ID {app_id} and Depot ID {depot_id}.")
            print(result.stdout)
        else:
            print(f"Error fetching manifest for App ID {app_id} and Depot ID {depot_id}.")
            print(result.stderr)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    fetch_manifest(APP_ID, DEPOT_ID, USERNAME, PASSWORD, BRANCH)
