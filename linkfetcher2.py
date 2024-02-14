import xml.etree.ElementTree as ET
import requests
import re
from urllib.parse import quote
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def fetch_and_parse_xml(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def preprocess_for_fuzzy(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.strip()

def is_excluded(file_name):
    """Check if the file name contains excluded terms within brackets."""
    excluded_terms = ['proto', 'beta', 'demo', 'sample', 'promo']
    for term in excluded_terms:
        if re.search(r'\b{}\b'.format(term), file_name, re.IGNORECASE):
            return True
    return False

def select_most_similar_file(game_title, files):
    preprocessed_title = preprocess_for_fuzzy(game_title)
    # Filter out files with excluded terms
    filtered_files = [f for f in files if not is_excluded(f)]
    preprocessed_files = [preprocess_for_fuzzy(f) for f in filtered_files]
    
    if not preprocessed_files:  # If all files are excluded, return None
        print(f"All files for '{game_title}' are excluded based on criteria.")
        return None, None
    
    best_match, score = process.extractOne(preprocessed_title, preprocessed_files, scorer=fuzz.token_sort_ratio)
    if best_match and score >= 70:  # Adjust score threshold as needed
        matched_index = preprocessed_files.index(best_match)
        original_file_name = filtered_files[matched_index]
        print(f"Matched '{game_title}' to '{original_file_name}' with a score of {score}")
        return original_file_name, score
    else:
        print(f"No match found for '{game_title}'")
        return None, None

def hail_mary_check(game_title, files):
    """Check if the exact game title is part of any file names."""
    for file in files:
        if game_title.lower() in file.lower():  # Case-insensitive comparison
            return file
    return None

def generate_download_links(game_titles, xml_data_urls):
    all_files = []

    # Fetch and combine files from all XML URLs
    for url in xml_data_urls:
        root = fetch_and_parse_xml(url)
        if root:
            all_files.extend([file.get('name') for file in root.findall('file')])
    
    # Sort the combined list of files alphabetically
    all_files_sorted = sorted(all_files, key=lambda x: x.lower())

    download_links = {}
    unmatched_titles = []
    hail_mary_matches = {}  # Store Hail Mary matches here

    for game_title in game_titles:
        selected_file, score = select_most_similar_file(game_title, all_files_sorted)
        if selected_file:
            part_after_items = url.split("/items/")[-1].split('/')[0]
            encoded_file_name = quote(selected_file)
            download_link = f"https://archive.org/download/{part_after_items}/{encoded_file_name}"
            download_links[game_title] = download_link
        else:
            # Attempt Hail Mary check
            hm_file = hail_mary_check(game_title, all_files_sorted)
            if hm_file:
                part_after_items = url.split("/items/")[-1].split('/')[0]
                encoded_file_name = quote(hm_file)
                download_link = f"https://archive.org/download/{part_after_items}/{encoded_file_name}"
                hail_mary_matches[game_title] = download_link
            else:
                unmatched_titles.append(game_title)

    # Writing matched and Hail Mary matched links to file
    with open("download_links.txt", "w") as file:
        for title, link in download_links.items():
            file.write(f"{title}: {link}\n")
        for title, link in hail_mary_matches.items():
            file.write(f"Hail Mary - {title}: {link}\n")

    return unmatched_titles, hail_mary_matches

if __name__ == "__main__":
    # Read game titles from a file
    with open("greatest_ps2.txt", "r") as file:
        game_titles = [line.strip() for line in file.readlines()]

    xml_data_urls = [
        "https://ia800505.us.archive.org/7/items/redumpSonyPlaystation2UsaGames2018Aug01/redumpSonyPlaystation2UsaGames2018Aug01_files.xml",
        "https://ia904703.us.archive.org/32/items/redumpSonyPlaystation2UsaGames2018Aug01Part2/redumpSonyPlaystation2UsaGames2018Aug01Part2_files.xml",
        "https://ia801005.us.archive.org/20/items/redumpSonyPlaystation2UsaGames2018Aug01Part3/redumpSonyPlaystation2UsaGames2018Aug01Part3_files.xml",
        "https://ia803004.us.archive.org/19/items/redumpSonyPlaystation2UsaGames2018Aug01Part4/redumpSonyPlaystation2UsaGames2018Aug01Part4_files.xml",
        "https://ia803009.us.archive.org/4/items/redumpSonyPlaystation2UsaOther2018Aug01/redumpSonyPlaystation2UsaOther2018Aug01_files.xml",
    ]

    unmatched_titles, hail_mary_matches = generate_download_links(game_titles, xml_data_urls)
    if unmatched_titles:
        print("Unmatched Titles:")
        for title in unmatched_titles:
            print(title)
    if hail_mary_matches:
        print("\nHail Mary Matches Found:")
        for title, link in hail_mary_matches.items():
            print(f"{title}: {link}")


