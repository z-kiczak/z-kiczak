import os
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from googlesearch import search
import textwrap
import re
import time
import random


def format(text):
    if text:
        return "\n".join(textwrap.wrap(text, width=70))
    else:
        return ""


def scrape_website_content(url):
    """Scrape main text content from website"""
    try:
        response = requests.get(url, timeout=10)  # Add timeout
        response.raise_for_status()  # Raise HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract first paragraph with sufficient text
        par = soup.find('p')
        if par and len(par.text.strip()) > 100:
            return par.text.strip()
        else:
            return ""  # Return empty if no valid paragraph

    except Exception as e:
        print(f"Scraping error for {url}: {e}")
        return ""  # Return empty string on failure


def fetch_additional_info(query):
    """Fetch information from Google search with randomized delays"""
    try:
        # Get top 5 search results
        urls = list(search(query, num_results=5, timeout=20))
        contents = []

        for url in urls:
            content = scrape_website_content(url)
            if content:  # Skip empty responses
                formatted = format(content)
                contents.append(formatted)

        return "\n\n".join(contents) if contents else "No information found"

    except Exception as e:
        print(f"Search error: {e}")
        return "Information unavailable"


def extract_table(soup):
    """
    Extract table data from HTML
    Returns: List of tuples containing table row data
    """
    try:
        table = soup.find('tbody')
        if not table:
            return None

        table_content = []
        # Process each table row
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if not cells:
                continue  # Skip header rows

            # Extract: Rank, Logo, Language, Rating, Change
            img_tag = cells[3].find('img')
            row_data = (
                cells[0].text.strip(),
                f"![Logo](https://www.tiobe.com{img_tag['src']})" if img_tag else "",
                cells[4].text.strip(),
                cells[5].text.strip(),
                cells[6].text.strip()
            )
            table_content.append(row_data)

        return table_content[:20]  # Return top 20 entries

    except Exception as e:
        print(f"Table extraction error: {e}")
        return None


def create_language_subsites(table_content):
    """Create individual markdown files for each language"""
    if not table_content:
        return

    for rank, logo, lang, rating, change in table_content:
        # Create filename from language name
        filename = re.sub(r'[^\w-]', '', lang.lower().replace(' ', '_')) + ".md"

        # Fetch additional information
        additional_info = fetch_additional_info(f"what is {lang} programming language?")
        if not additional_info: additional_info = "No additional details available.\n"

        # Create markdown content
        content = [
            f"# {lang} Programming Language\n\n",
            logo + "\n\n" if logo else "",
            f"**Rank:** {rank}\n\n",
            f"**Rating:** {rating}\n\n",
            f"**Change:** {change}\n\n",
            "## Additional Information\n\n",
            additional_info + "\n\n",
            f"[Back to main rankings](../tiobe_main.md)"
        ]

        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("".join(content))

        print(f"Created subsite for {lang} at {filename}")


def create_site(main_url):
    """
    Main function to create markdown documentation
    Args:
        main_url: URL of the page to scrape
    """
    try:
        # Fetch and parse main page
        response = requests.get(main_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Initialize main content components
        main_md = []

        # Add main header
        h1 = soup.find('h1')
        if h1:
            main_md.append(f"# {h1.text.strip()}\n\n")

        # Add the paragraph starting with "The TIOBE"
        all_ps = soup.find_all('p')
        if all_ps:
            main_md.append(textwrap.fill(all_ps[4].text.strip(), width=70) + "\n\n")

        # Extract and process main table
        table_content = extract_table(soup)
        if table_content:
            main_md.append("\n## Top Languages Ranking\n")
            for rank, logo, lang, rating, change in table_content[:5]:
                # Create link to language subsite
                filename = re.sub(r'[^\w-]', '', lang.lower().replace(' ', '_')) + ".md"
                main_md.append(
                    f"**{rank}.** {logo} [{lang}]({filename})  \n"
                    f"Rating: {rating} | Change: {change}\n\n"
                )

            # Create individual language subsites
            create_language_subsites(table_content)

        # Write main markdown file
        with open('tiobe_main.md', 'w', encoding='utf-8') as f:
            f.write("".join(main_md))

        print("Main site and language subsites created successfully!")

    except Exception as e:
        print(f"Site creation failed: {e}")
        with open('tiobe_main.md', 'w') as f:
            f.write(f"# Error\nCould not generate documentation: {str(e)}")


if __name__ == '__main__':
    # Example usage
    create_site(
        main_url="https://www.tiobe.com/tiobe-index/"
    )