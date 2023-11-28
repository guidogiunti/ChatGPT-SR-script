import json
import pandas as pd
import ssl
import time
import termcolor
import os
from Bio import Entrez
from google_play_scraper import Sort, reviews, app, search
from termcolor import colored
from tqdm import tqdm


# Create a SSLContext object for Python stdlib modules
ssl._create_default_https_context = ssl._create_unverified_context

# Replace with your email for Entrez
Entrez.email = "YOUREMAILHERE"

# List of country codes to search in
countries = ["us", "ca", "gb", "au", "nz", "ie", "in", "sg", "za", "gh", "ng", "ke", "tz", "ug", "zm", "mw", "mu", "bw", "sz", "na", "lr", "sl", "gm", "sn", "bj", "gh", "ci", "tg", "bf", "ne", "mg", "mr", "gn", "gw", "ml", "gm", "km", "dj", "mu", "sc", "sd", "rw", "ug", "et", "er", "so", "dj", "yt", "re", "km", "mg", "sc", "na", "bw", "zw", "zm", "ls", "mz"]

def clear_terminal():
    if os.name == "nt":
        os.system("cls")
    # For Linux and macOS
    else:
        os.system("clear")

# Call the function before printing the statement
clear_terminal()

# Describe what the script does
print(colored("The script will look for MS apps on the Google Play Stores of English speaking countries, remove any duplicates and see if the apps have any evidence claims based on a keywords list. Afterwards, it will try to find mentions by name of the apps in PubMed and generate CSV files with the information.", "white"))
print(colored("Should we start? (y/n)", "yellow"))
choice = input().lower()
if choice == "y":
    print(colored("Running script...", "yellow"))
else:
    # Exit the script if the user does not want to continue
    print(colored("Operation cancelled by user.", "red"))
    exit()

# Search Google Play Store for apps targeting people with multiple sclerosis
query = "multiple sclerosis"
with tqdm(total=len(countries), unit="country", desc=colored("---> Searching Google Play Store for MS apps", "yellow"), bar_format="{desc}: \033[33m{bar}\033[0m {percentage:3.0f}%|") as pbar:
    for country in countries:
        while True:
            try:
                result = search(query, lang="en", country=country)
                pbar.update(1)
                break
            except TimeoutError:
                print(colored("Timeout occurred. Would you like to wait a little longer? (y/n)", "yellow"))
                choice = input().lower()
                if choice == "y":
                    print(colored("Waiting for 10 seconds...", "yellow"))
                    time.sleep(10)
                else:
                    break

if result:
    print(colored("Google Play Store search successful!", "green"))
     # Check if file already exists
    filename = "multiple_sclerosis_apps.csv"
    if os.path.isfile(filename):
        print(colored(f"The file {filename} already exists. Do you want to overwrite it? (y/n)", "red"))
        choice = input().lower()
        if choice == "y":
            print(colored("Overwriting existing file...", "yellow"))
        else:
        # Exit the script if the user does not want to overwrite the file
            print(colored("Operation cancelled by user.", "red"))
            exit()

    # Extract app data
    app_data = []
    # Read keywords from csv file
    keywords_df = pd.read_csv("keywords.csv")
    medical_keywords = list(keywords_df["Keywords"])
    
    with tqdm(total=100, unit="items" , desc=colored("---> Looking for evidence claims in app descriptions", "yellow"), bar_format="{desc}: \033[33m{bar}\033[0m {percentage:3.0f}|{bar}") as pbar:

        for item in result[:250]:  # Limit to the first 250 results
            name = item["title"]
            link = "https://play.google.com/store/apps/details?id=" + item["appId"]
            description = item["description"]
            pbar.update(1)

            # Check for medical or clinical evidence
            medical_evidence = "Yes" if any(keyword in description.lower() for keyword in medical_keywords) else "No"

            app_data.append([name, link, description, medical_evidence])


    # Create a DataFrame and save it to a CSV file
    app_df = pd.DataFrame(app_data, columns=["Name", "Link", "Description", "Medical Evidence"])
    print(colored("---> Removing duplicates...", "yellow"))
    app_df.drop_duplicates(subset="Name", inplace=True)  # Remove duplicates based on app name
    app_df.to_csv("multiple_sclerosis_apps.csv", index=False)
    print(colored(f"{len(app_data)} apps were found and saved to 'multiple_sclerosis_apps.csv'.", "green"))
else:
    print(colored("Google Play Store search failed.", "red"))

# Search PubMed for scientific publications related to the apps
pubmed_data = []
pubmed_filename = "app_pubmed_references.csv"

while True:
    try:
        total_pubmed = len(app_df) * 100
        with tqdm(total=total_pubmed, unit="items" , desc=colored("---> Searching PubMed for scientific publications related to the apps", "yellow"), bar_format="{desc}: \033[33m{bar}\033[0m {percentage:3.0f}|") as pbar:

            for app_name in app_df["Name"]:
                search_results = Entrez.read(Entrez.esearch(db="pubmed", term=f'"{app_name}"[All Fields]', retmax=100))
                pubmed_ids = search_results["IdList"]

                for pubmed_id in pubmed_ids:
                    pubmed_data.append([app_name, pubmed_id])
                    pbar.update(1)

        if os.path.isfile(pubmed_filename):
                print(colored(f"The file {pubmed_filename} already exists. Do you want to overwrite it? (y/n)", "red"))
                choice = input().lower()
                if choice == "y":
                    print(colored("Overwriting existing file...", "yellow"))
                else:
                # Exit the script if the user does not want to overwrite the file
                    print(colored("Operation cancelled by user.", "red"))
                    exit()

        # Create a DataFrame and save it to a CSV file
        pubmed_df = pd.DataFrame(pubmed_data, columns=["App Name", "PubMed ID"])
        print(colored("---> Removing duplicates...", "yellow"))
        pubmed_df.drop_duplicates(inplace=True)  # Remove duplicates based on app name and PubMed ID
        pubmed_df.to_csv("app_pubmed_references.csv", index=False)
        print(colored(f"{len(pubmed_data)} pubmed references were found and saved to 'app_pubmed_references.csv'.", "green"))

        break
    except TimeoutError:
        print(colored("Timeout occurred. Would you like to wait a little longer? (y/n)", "yellow"))
        choice = input().lower()
        if choice == "y":
            print(colored("Waiting for 10 seconds...", "yellow"))
            time.sleep(10)
        else:
            break
