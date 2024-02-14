import xml.etree.ElementTree as ET
import requests
import re
from urllib.parse import quote

# Function to fetch and parse XML from a given URL
def fetch_and_parse_xml(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

# Normalize titles for comparison
def normalize_title(title):
    return title.lower().strip()
 
def select_file_with_highest_version(files):
    highest_version_file = None
    highest_version = 0.0  # Initialize to 0.0 for comparison
    
    # For debugging: Track all considered versions
    considered_versions = {}

    for file in files:
        # Skip files explicitly marked as demo
        if "demo" in file.lower():
            continue

        # Try to find a version number in the file name
        version_match = re.search(r'\bv(\d+\.\d+)', file, re.IGNORECASE)
        if version_match:
            version = float(version_match.group(1))
            considered_versions[file] = version  # Track considered version
            
            if version > highest_version:
                highest_version = version
                highest_version_file = file
                print(f"New highest version found: {version} in file {file}")  # Debugging output

    if considered_versions:
        # Print the header only if there are considered versions
        print("Considered versions and files:")
        for file, version in considered_versions.items():
            print(f"{file}: v{version}")
    else:
        # If no versioned file was found and the list isn't empty, indicate the defaulting decision
        if files:
            highest_version_file = files[0]  # Default to the first file if no versions are found
            print(f"No versioned file found, defaulting to single-bracket file: {highest_version_file}")

    # After the selection process, indicate the final choice
    if highest_version_file:
        print(f"Final file selected: {highest_version_file}")
    else:
        print("No suitable file was selected.")

    return highest_version_file


def normalize_string(input_string):
    # Normalize dashes as before and trim whitespace
    normalized_string = input_string.replace("–", "-").replace("—", "-").strip()
    return normalized_string
    
def generate_download_links(game_titles, xml_roots, base_urls):
    download_links = {}
    partial_matches = {}  # Initialize to track partial matches
    potential_files = {title: [] for title in game_titles}  # Prepare to collect files for each title

    for base_url, root in zip(base_urls, xml_roots):
        for file in root.findall('file'):
            file_name = file.get('name').lower()
            
            # Check each game title for a potential match without immediately deciding
            for game_title in game_titles:
                normalized_game_title = re.escape(normalize_title(game_title))
                pattern = '^' + normalized_game_title + r'(?:(?:\s+\(.*?\))*.7z)$'
                if re.search(pattern, file_name, re.IGNORECASE):
                    # Collect potential files instead of deciding immediately
                    potential_files[game_title].append(file_name)
    
    # Now, apply selection logic to each collected list of potential files
    for game_title, files in potential_files.items():
        if files:  # If there are potential files for this title
            selected_file = select_file_with_highest_version(files)
            if selected_file:
                # If a file is selected, it's no longer considered a partial match, hence removed from partial matches if exists
                partial_matches.pop(game_title, None)
                # Construct the download link for the selected file
                part_after_items = base_urls[0].split("/items/")[-1].split('/')[0]  # Assuming all URLs follow a similar structure
                encoded_file_name = quote(selected_file)
                download_link = f"https://archive.org/download/{part_after_items}/{encoded_file_name}"
                download_links[game_title] = download_link
        else:
            # If no files are found for a title, it could be considered a partial match or excluded
            partial_matches[game_title] = "No files found"

    # Determine which titles were excluded based on files found
    excluded_titles = [title for title in game_titles if title not in download_links and title not in partial_matches]

    return download_links, partial_matches, sorted(excluded_titles)

# Main execution block
if __name__ == "__main__":
    # Read game titles from a file
    with open("greatest_ps2.txt", "r") as file:
        game_titles = [line.strip() for line in file.readlines()]

    # Base URLs for XML data
    xml_data_urls = [
        "https://ia800505.us.archive.org/7/items/redumpSonyPlaystation2UsaGames2018Aug01/redumpSonyPlaystation2UsaGames2018Aug01_files.xml",
        "https://ia904703.us.archive.org/32/items/redumpSonyPlaystation2UsaGames2018Aug01Part2/redumpSonyPlaystation2UsaGames2018Aug01Part2_files.xml",
        "https://ia801005.us.archive.org/20/items/redumpSonyPlaystation2UsaGames2018Aug01Part3/redumpSonyPlaystation2UsaGames2018Aug01Part3_files.xml",
        "https://ia803004.us.archive.org/19/items/redumpSonyPlaystation2UsaGames2018Aug01Part4/redumpSonyPlaystation2UsaGames2018Aug01Part4_files.xml",
        "https://ia803009.us.archive.org/4/items/redumpSonyPlaystation2UsaOther2018Aug01/redumpSonyPlaystation2UsaOther2018Aug01_files.xml",
    ]

    # Corresponding base URLs for constructing download links
    base_download_urls = [url.rsplit('/', 1)[0] for url in xml_data_urls]

    # Fetch and parse XML data
    xml_roots = [fetch_and_parse_xml(url) for url in xml_data_urls]

    # Filter out any None values in case of fetch errors
    xml_roots = [root for root in xml_roots if root is not None]

    # Generate and print download links
    download_links, partial_matches, excluded_titles = generate_download_links(game_titles, xml_roots, base_download_urls)

    # Write download links to file
    with open("download_links.txt", "w") as file:
        for title, link in download_links.items():
            file.write(f"{link}\n")

    # Output partial matches
    if partial_matches:
        print("\nPartially Matched Titles:")
        for title, file_name in partial_matches.items():
            print(f"{title} was partially matched with {file_name}")

    # Output excluded titles
    if excluded_titles:
        print("\nExcluded Titles (No Matches Found):")
        for title in excluded_titles:
            print(title)
    else:
        print("\nAll titles were successfully matched or partially matched.")
