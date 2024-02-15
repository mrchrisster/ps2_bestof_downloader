import xml.etree.ElementTree as ET
import requests
import re
from urllib.parse import quote
from fuzzywuzzy import fuzz, process

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
    pattern = r'\((.*?)\)'  # Matches any content within brackets
    matches = re.findall(pattern, file_name, re.IGNORECASE)
    for match in matches:
        for term in excluded_terms:
            if term in match.lower():  # Checks if the term is in the matched bracket content
                return True
    return False
    
def extract_numbers(text):
    """Extracts all numbers from a given text."""
    return re.findall(r'\d+', text)
    
def select_most_similar_file(game_title, files):
    preprocessed_title = preprocess_for_fuzzy(game_title)
    title_numbers = extract_numbers(game_title)
    filtered_files = [f for f in files if not is_excluded(f)]

    best_match = None
    best_score = -1  # Initialize with an invalid score

    for file in filtered_files:
        # Process filename to consider text up to the first "("
        file_base = file.split("(")[0].strip()
        file_numbers = extract_numbers(file_base)

        # Rule 1 & 2: Skip files where numeric parts don't match or don't align with the title's numbers
        if title_numbers != file_numbers:
            continue

        # Perform fuzzy matching on processed strings
        preprocessed_file = preprocess_for_fuzzy(file_base)
        score = fuzz.token_sort_ratio(preprocessed_title, preprocessed_file)

        # Update best match if this file has a higher score than current best
        if score > best_score:
            best_match = file
            best_score = score

    if best_match and best_score >= 70:  # Consider matches above a certain threshold
        print(f"Matched '{game_title}' to '{best_match}' with a score of {best_score}")
        return best_match, best_score
    else:
        print(f"No match found for '{game_title}'")
        return None, None
  
def generate_download_links(game_titles, xml_data_urls, input_filename):
    all_files = []
    for url in xml_data_urls:
        root = fetch_and_parse_xml(url)
        if root:
            all_files.extend([file.get('name') for file in root.findall('file')])
    
    all_files_sorted = sorted([f for f in all_files if not is_excluded(f)], key=lambda x: x.lower())

    matched_games = {}  # Store matched games as {game_title: matched_file}
    unmatched_titles = []  # List to store unmatched game titles

    for game_title in game_titles:
        selected_file, score = select_most_similar_file(game_title, all_files_sorted)
        if selected_file:
            matched_games[game_title] = selected_file
        else:
            unmatched_titles.append(game_title)

    # Sort matched games alphabetically by game title
    sorted_matched_games = {k: matched_games[k] for k in sorted(matched_games)}

    # Create log filename based on input filename with "_log" appended
    log_filename = f"{input_filename.rsplit('.', 1)[0]}_log.txt"

    # Write matched games and unmatched titles to log file, sorted alphabetically
    with open(log_filename, "w") as log_file:
        log_file.write("Matched Titles and Files:\n")
        for title, filename in sorted_matched_games.items():
            log_file.write(f"Title: {title}\nMatched File: {filename}\n\n")
        
        if unmatched_titles:
            log_file.write("Unmatched Titles:\n")
            for title in sorted(unmatched_titles):
                log_file.write(f"{title}\n")

    return unmatched_titles, sorted_matched_games

if __name__ == "__main__":
    input_filename = "greatest_ps2.txt"
    with open(input_filename, "r") as file:
        game_titles = [line.strip() for line in file.readlines()]

    xml_data_urls = [
        "https://ia800505.us.archive.org/7/items/redumpSonyPlaystation2UsaGames2018Aug01/redumpSonyPlaystation2UsaGames2018Aug01_files.xml",
        "https://ia904703.us.archive.org/32/items/redumpSonyPlaystation2UsaGames2018Aug01Part2/redumpSonyPlaystation2UsaGames2018Aug01Part2_files.xml",
        "https://ia801005.us.archive.org/20/items/redumpSonyPlaystation2UsaGames2018Aug01Part3/redumpSonyPlaystation2UsaGames2018Aug01Part3_files.xml",
        "https://ia803004.us.archive.org/19/items/redumpSonyPlaystation2UsaGames2018Aug01Part4/redumpSonyPlaystation2UsaGames2018Aug01Part4_files.xml",
        "https://ia803009.us.archive.org/4/items/redumpSonyPlaystation2UsaOther2018Aug01/redumpSonyPlaystation2UsaOther2018Aug01_files.xml",
    ]

    unmatched_titles, matched_games = generate_download_links(game_titles, xml_data_urls, input_filename)