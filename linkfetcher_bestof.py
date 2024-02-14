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
    single_bracket_files = []
    multi_bracket_files = []
    highest_version = "0.00"
    highest_version_file = None

    # Categorize files based on the number of bracket sets
    for file in files:
        if file.count('(') == 1:
            single_bracket_files.append(file)
        else:
            multi_bracket_files.append(file)

    # Process multi-bracket files to find the highest version
    for file in multi_bracket_files:
        version_numbers = re.findall(r'\(v(\d+\.\d+)\)', file)
        if version_numbers:
            version = max(version_numbers, key=lambda x: float(x))
            if version > highest_version:
                highest_version = version
                highest_version_file = file
    
    # If no suitable multi-bracket file is found, consider single bracket files
    if not highest_version_file and single_bracket_files:
        # Prefer single bracket set if it's the only option or if multi-bracket files don't contain versions
        return single_bracket_files[0]  # Assuming single bracket files are equally suitable; adjust as needed

    return highest_version_file

def normalize_string(input_string):
    # Normalize dashes as before and trim whitespace
    normalized_string = input_string.replace("–", "-").replace("—", "-").strip()
    return normalized_string
    
def generate_download_links(game_titles, xml_roots, base_urls):
    download_links = {}
    excluded_titles = set(game_titles)  # Start with all titles considered as excluded
    partial_matches = {}  # To track titles that matched partially

    for base_url, root in zip(base_urls, xml_roots):
        for file in root.findall('file'):
            file_name = file.get('name')

            # Skip files marked as demos
            if "(demo)" in file_name.lower():
                continue  # Skip this file and proceed to the next one

            for game_title in game_titles:
                normalized_game_title = re.escape(game_title.lower())
                pattern = '^' + normalized_game_title + r'(?:(?:\s+\(.*?\))*.7z)$'
                if re.search(pattern, file_name, re.IGNORECASE):
                    excluded_titles.discard(game_title)  # Found an exact match

                    # URL-encode file name and construct download link
                    part_after_items = base_url.split("/items/")[-1].split('/')[0]
                    encoded_file_name = quote(file_name)  # URL-encode the file name
                    download_link = f"https://archive.org/download/{part_after_items}/{encoded_file_name}"
                    download_links[game_title] = download_link  # Store the download link

    # Second pass for partial matches among the titles not matched exactly
    for game_title in list(excluded_titles):  # Work on a copy since we'll modify the set during iteration
        for base_url, root in zip(base_urls, xml_roots):
            for file in root.findall('file'):
                file_name = file.get('name')
                if "(demo)" in file_name.lower():
                    continue  # Again, skip demo files

                # Check for partial match, excluding demos explicitly
                if game_title.lower() in file_name.lower():
                    excluded_titles.discard(game_title)
                    partial_matches[game_title] = file_name

                    # Construct download link for partial match, with URL encoding
                    part_after_items = base_url.split("/items/")[-1].split('/')[0]
                    encoded_file_name = quote(file_name)
                    download_link = f"https://archive.org/download/{part_after_items}/{encoded_file_name}"
                    download_links[game_title] = download_link

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
