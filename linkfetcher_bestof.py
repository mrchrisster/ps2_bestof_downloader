import xml.etree.ElementTree as ET
import requests
import re

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
    """
    Selects the file with the highest version number from a list of files.
    If no version number is present, defaults to a basic comparison.
    """
    highest_version_file = None
    highest_version = "0.00"  # Default version

    for file in files:
        # Extract version numbers, assuming they are in the format (vX.XX)
        version_match = re.search(r'\(v(\d+\.\d+)\)', file)
        version = version_match.group(1) if version_match else "0.00"

        if version > highest_version or not highest_version_file:
            highest_version = version
            highest_version_file = file

    return highest_version_file

def normalize_string(input_string):
    # Normalize dashes as before and trim whitespace
    normalized_string = input_string.replace("–", "-").replace("—", "-").strip()
    return normalized_string

def generate_download_links(game_titles, xml_roots, base_urls):
    download_links = {}
    excluded_titles = set(game_titles)  # Initially assume all titles are excluded
    partial_matches = {}  # To track titles that were matched partially

    # First pass: Attempt to find exact matches
    for base_url, root in zip(base_urls, xml_roots):
        for file in root.findall('file'):
            file_name = file.get('name')

            for game_title in game_titles:
                normalized_game_title = re.escape(game_title.lower())
                pattern = '^' + normalized_game_title + r'(?:(?:\s+\(.*?\))*.7z)$'
                if re.search(pattern, file_name, re.IGNORECASE):
                    excluded_titles.discard(game_title)  # Found an exact match
                    # Store the download link as before...

    # Second pass: Attempt to find partial matches for remaining titles
    for game_title in excluded_titles.copy():  # Work on a copy since we'll modify the set during iteration
        for base_url, root in zip(base_urls, xml_roots):
            for file in root.findall('file'):
                file_name = file.get('name')
                if game_title.lower() in file_name.lower():
                    excluded_titles.discard(game_title)  # Found a partial match
                    partial_matches[game_title] = file_name  # Track the partial match
                    # Construct and store the download link as before...

    return download_links, partial_matches, sorted(list(excluded_titles))


    
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
