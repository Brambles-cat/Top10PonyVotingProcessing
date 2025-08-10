"""Module that contains global variables that may be needed in several project files"""

import os, sys

# unfrozen is used to indicate when the program is being ran from main.py
# rather than from a .exe file
unfrozen = not getattr(sys, 'frozen', False)

# URL to the downloadable CSV export of the master Top 10 Pony Videos List.
top_10_archive_csv_url = "https://docs.google.com/spreadsheets/d/1rEofPkliKppvttd8pEX8H6DtSljlfmQLdFR-SlyyX7E/export?format=csv"

# URL to the downloadable CSV export of the honorable mentions list.
honorable_mentions_csv_url = "https://docs.google.com/spreadsheets/d/1rEofPkliKppvttd8pEX8H6DtSljlfmQLdFR-SlyyX7E/export?format=csv&gid=841236474#gid=841236474"

# Path to a local copy of the master Top 10 Pony Videos List (in CSV format).
local_top_10_archive_csv_path = unfrozen * "data/" + "top_10_master_archive.csv"

# Path to a local copy of the honorable mentions list (in CSV format).
local_honorable_mentions_csv_path = unfrozen * "data/" + "honorable_mentions_archive.csv"

ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "retries": 3,
    "sleep_interval": 2,
    "allowed_extractors": [
        "twitter",
        "Newgrounds",
        "lbry", # Odysee
        "TikTok",
        "PeerTube", # pony.tube & pt.thishorsie.rocks
        "vimeo",
        "BiliBili",
        "dailymotion",
        "Bluesky",
        "generic", # ytdlp may fall back to the generic extractor if another fails
    ],
}

# Previously, some twitter requests returned no data due to content being restricted
if os.path.exists("data/cookies.txt"):
    ydl_opts["cookiefile"] = "data/cookies.txt"
