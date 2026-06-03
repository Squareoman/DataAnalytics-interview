import re
import requests
from bs4 import BeautifulSoup


def decode_secret_message(url: str) -> None:
    # Normalise the URL so we always hit the published HTML endpoint.
    # Published docs use /d/e/LONG_ID/pub; regular docs use /d/SHORT_ID/edit|view.
    if url.rstrip("/").endswith("/pub"):
        fetch_url = url  # already a published URL — use as-is
    else:
        # Extract the document ID from a standard edit/view URL and publish it.
        doc_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            fetch_url = f"https://docs.google.com/document/d/{doc_id}/pub"
        else:
            fetch_url = url  # fall back to whatever was passed

    response = requests.get(fetch_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise ValueError("No table found in the document.")

    rows = table.find_all("tr")

    # Parse every row after the header row.
    data: list[tuple[int, str, int]] = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        x_text = cols[0].get_text(strip=True)
        char = cols[1].get_text(strip=True)
        y_text = cols[2].get_text(strip=True)

        if not x_text or not y_text:
            continue
        try:
            data.append((int(x_text), char if char else " ", int(y_text)))
        except ValueError:
            continue  # skip malformed rows

    if not data:
        raise ValueError("No character data found in the table.")

    max_x = max(x for x, _, _ in data)
    max_y = max(y for _, _, y in data)

    # Build the grid, defaulting every cell to a space.
    grid = [[" "] * (max_x + 1) for _ in range(max_y + 1)]

    for x, char, y in data:
        grid[y][x] = char

    # y=0 is the bottom row (y increases upward), so print from max_y down to 0.
    for row in reversed(grid):
        print("".join(row))


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        decode_secret_message(sys.argv[1])
    else:
        doc_url = input("Enter Google Doc URL: ").strip()
        decode_secret_message(doc_url)
