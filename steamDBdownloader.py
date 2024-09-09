import os
import requests
import subprocess
import keyring
import json
import logging
from getpass import getpass
from tqdm import tqdm
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(filename='steamdb_downloader_debug.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

# Constants
SERVICE_NAME = "DepotDownloader"
STEAM_API_KEY = os.environ.get("SteamAPI")  # Fetch Steam API key from environment variable
CACHE_FILE = "app_cache.json"  # File to store App IDs and Depot IDs
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"

# Get the current working directory where your Python script is running
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the path to DepotDownloader.exe
DEPOT_DOWNLOADER_PATH = os.path.join(current_dir, "DepotDownloader.exe")


# Function to get depot list from SteamDB
def get_depot_list_from_app(app_id):
    url = f"https://steamdb.info/app/{app_id}/depots/"
    logging.debug(f"Fetching depots from: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error fetching data from {url}: {str(e)}")
        return []

    soup = BeautifulSoup(response.content, "lxml")
    depots = []

    depot_table = soup.find("table", {"class": "table-depot-table"})
    if depot_table:
        rows = depot_table.find_all("tr")[1:]  # Skip the header row
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                depot_id = cols[0].text.strip()
                depot_name = cols[1].text.strip()
                depots.append({"id": depot_id, "name": depot_name})
                logging.debug(f"Found depot: {depot_id} - {depot_name}")
    else:
        logging.debug(f"No depot table found for app {app_id}")

    if not depots:
        logging.warning(f"No depots found for App ID {app_id} on SteamDB.")

    return depots


# Function to display depot list
def display_depot_list(depots):
    if depots:
        print(f"Found {len(depots)} depots:")
        for idx, depot in enumerate(depots, 1):
            print(f"{idx}. Depot ID: {depot['id']}, Name: {depot['name']}")
    else:
        print("No depot information available.")
        logging.debug("No depots to display.")


# Function to remove duplicates from the app list
def remove_duplicates(app_list):
    unique_apps = []
    seen_ids = set()
    for app in app_list:
        if app['appid'] not in seen_ids:
            unique_apps.append(app)
            seen_ids.add(app['appid'])
            logging.debug(f"Adding unique app: {app['name']} (App ID: {app['appid']})")
    return unique_apps


# Function to search for App ID by game name and list all matching results
def search_app_ids(game_name):
    url = f"https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    logging.debug(f"Fetching app list from Steam API: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error fetching app list from {url}: {str(e)}")
        return []

    app_list = response.json()

    matching_apps = []
    for app in app_list["applist"]["apps"]:
        if game_name.lower() in app["name"].lower():
            matching_apps.append({"name": app["name"], "appid": app["appid"]})

    # Remove duplicate app IDs
    matching_apps = remove_duplicates(matching_apps)

    if matching_apps:
        print(f"Found {len(matching_apps)} matching apps for '{game_name}':")
        for idx, app in enumerate(matching_apps, 1):
            print(f"{idx}. {app['name']} (App ID: {app['appid']})")
        return matching_apps
    else:
        print(f"No App ID found for game: {game_name}")
        logging.debug(f"No matching apps found for game: {game_name}")
        return None


# Function to get or set Steam credentials securely
def get_credentials():
    username = keyring.get_password(SERVICE_NAME, "username")
    password = keyring.get_password(SERVICE_NAME, "password")

    if not username:
        username = input("Enter your Steam username: ")
        keyring.set_password(SERVICE_NAME, "username", username)
        logging.debug(f"Saved Steam username: {username}")

    if not password:
        password = getpass("Enter your Steam password: ")
        keyring.set_password(SERVICE_NAME, "password", password)
        logging.debug("Saved Steam password.")

    return username, password


# Function to download depot using DepotDownloader with saved credentials
def download_depot(app_id, depot_id, manifest_id=None):
    username, password = get_credentials()

    logging.debug(f"Starting depot download for App ID: {app_id}, Depot ID: {depot_id}")
    depot_command = [
        DEPOT_DOWNLOADER_PATH,
        "-app", app_id,
        "-depot", depot_id,
        "-username", username,
        "-password", password,
        "-remember-password"
    ]
    if manifest_id:
        depot_command.extend(["-manifest", manifest_id])
        logging.debug(f"Using manifest ID: {manifest_id}")

    process = subprocess.Popen(depot_command, stdout=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode(), end="")
    process.wait()
    logging.debug("Depot download completed.")


# Function to track total download size using tqdm for progress tracking
def track_download_size(total_size):
    downloaded = 0
    with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading files") as progress_bar:
        while downloaded < total_size:
            progress_bar.update(512)  # Adjust this value based on actual data transfer
            downloaded += 512


# Function to cache App ID and Depot ID in a JSON file for future runs
def save_to_cache(game_name, app_id, depot_id):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
    else:
        cache = {}

    cache[game_name] = {"app_id": app_id, "depot_id": depot_id}
    logging.debug(f"Caching App ID {app_id} and Depot ID {depot_id} for game: {game_name}")

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)


# Function to check cache for existing App ID and Depot ID
def load_from_cache(game_name):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        if game_name in cache:
            print(f"Using cached App ID and Depot ID for {game_name}")
            logging.debug(f"Loaded cached App ID and Depot ID for game: {game_name}")
            return cache[game_name]["app_id"], cache[game_name]["depot_id"]
    return None, None


if __name__ == "__main__":
    # Prompt the user to input a game name
    game_name = input("Enter the name of the game you want to download: ")

    # Check cache for existing App ID and Depot ID
    app_id, depot_id = load_from_cache(game_name)

    # If not in cache, search for the App IDs and let the user select one
    if not app_id:
        matching_apps = search_app_ids(game_name)
        if matching_apps:
            selected_index = int(input("Select the app you want to download by number: ")) - 1
            app_id = matching_apps[selected_index]["appid"]

            # Fetch depot information for the selected App ID from SteamDB
            depots = get_depot_list_from_app(app_id)
            display_depot_list(depots)

            # Prompt user to select a depot from the list
            if depots:
                selected_depot_index = int(input("Select the depot you want to download by number: ")) - 1
                depot_id = depots[selected_depot_index]["id"]

                # Save the selected App ID and Depot ID in the cache
                save_to_cache(game_name, app_id, depot_id)
            else:
                print(f"No depots found for App ID {app_id}. Exiting.")
                logging.debug(f"No depots found for App ID {app_id}.")
                exit(1)
        else:
            print("Could not find any matching App IDs. Exiting.")
            logging.debug(f"Could not find any matching App IDs for game: {game_name}. Exiting.")
            exit(1)

    # Fetch depot info (this step is just for URL display, actual download happens later)
    depot_url = f"https://steamdb.info/depot/{depot_id}/"
    print(f"Depot info URL: {depot_url}")

    # Example: Manually enter the total size for tracking purposes
    total_size_in_bytes = 500 * 1024 * 1024  # Example: 500 MB

    # Track download size progress (example usage)
    track_download_size(total_size_in_bytes)

    # Download depot
    download_depot(app_id, depot_id)
