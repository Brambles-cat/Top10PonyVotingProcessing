"""Functions for calculating video rankings based on number of votes."""

from datetime import datetime
from classes.typing import ArchiveRecord
from functions.general import sample_item_without_replacement
from functions.messages import err
from data.globals import local_top_10_archive_csv_path


def process_shifted_voting_data(rows: list[list[str]]) -> list[list[str]]:
    """Given a set of data obtained from a "shifted" CSV (ie. a votes CSV with
    annotation columns inserted after every original column), return a list of
    rows containing just the data fields, with the "shifted" cells removed."""
    # Remove the header row
    data_rows = rows[1:]

    # Ignore the first column and odd-indexed columns
    data_rows = [row[2::2] for row in data_rows]

    return data_rows


def get_titles_to_urls_mapping(
    title_rows: list[list[str]], url_rows: list[list[str]]
) -> dict[str, str]:
    """Given a set of (unshifted) title rows and a matching set of URL rows,
    return a dictionary that maps each title to its corresponding URL."""
    titles_to_urls = {}

    for title_row, url_row in zip(title_rows, url_rows, strict=True):
        for title, url in zip(title_row, url_row):
            titles_to_urls[title] = url

    return titles_to_urls


def get_titles_to_uploaders(
    titles_to_urls: dict[str, str], videos_data: dict[str, dict]
) -> dict[str, str]:
    """Given a dictionary mapping titles to urls, look up the
    return a dictionary that maps each title to its corresponding URL."""

    titles_to_uploaders = {}

    for title, url in titles_to_urls.items():
        video_data = videos_data[url]
        titles_to_uploaders[title] = (
            video_data["uploader"] if video_data is not None else None
        )

    return titles_to_uploaders


def calc_ranked_records(
    title_rows: list[list[str]],
    titles_to_urls: dict[str, str],
    titles_to_uploaders: dict[str, str],
) -> list[dict]:
    """Given a list of title rows, where each row represents the titles voted on
    in one ballot, calculate the frequency of occurrence of each title and
    generate a set of data records for the top 10 spreadsheet, ranked by
    percentage."""
    title_counts = {}
    for title_row in title_rows:
        for title in title_row:
            if title not in title_counts:
                title_counts[title] = 0
            title_counts[title] += 1

    if "" in title_counts:
        del title_counts[""]

    counted_voters = 0
    for i, title_row in enumerate(title_rows):
        vote_count = len(list(filter(lambda title: title, title_row)))
        if vote_count >= 5:
            counted_voters += 1
            continue

        if vote_count != 0:
            # +1 since most editors display 1 as the starting index and +1 to skip header
            raise ValueError(
                f"Only {vote_count} votes included in ballot line ~{i + 2} when at least 5 are required"
            )

    title_percentages = {
        title: (count / counted_voters) * 100 for title, count in title_counts.items()
    }

    # If any titles have the same percentage of votes, then they are tied, and
    # we need to break such ties in order to produce a ranked top 10. To do this
    # we group each title by its percentage, then build a ranked top 10 by
    # randomly sampling each group, highest percentage first.
    percentage_groups = {}
    for title, percentage in title_percentages.items():
        if percentage not in percentage_groups:
            percentage_groups[percentage] = []
        percentage_groups[percentage].append(title)

    sorted_percentages = sorted(percentage_groups, reverse=True)

    ranked_titles = []
    tie_broken = {}

    for percentage in sorted_percentages:
        percentage_group = percentage_groups[percentage]
        tie_break_needed = len(percentage_group) > 1
        while len(percentage_group) > 0:
            sampled_title = sample_item_without_replacement(percentage_group)
            ranked_titles.append(sampled_title)
            tie_broken[sampled_title] = False
            if tie_break_needed:
                tie_broken[sampled_title] = True

    records = []
    for title in ranked_titles:
        uploader = titles_to_uploaders[title]
        record = {
            "Title": title,
            "Uploader": uploader if uploader is not None else "",
            "Percentage": f"{title_percentages[title]:.4f}%",
            "Total Votes": title_counts[title],
            "URL": titles_to_urls[title],
            "Notes": "Tie broken randomly by computer" if tie_broken[title] else "",
        }

        records.append(record)

    return records


def get_history(
    archive_records: list[ArchiveRecord], from_date: datetime, anniversaries: list[int]
) -> dict[int, dict]:
    """Given a set of archive records (in the format specified by the header of
    the Top 10 Pony Videos master archive), return all records which occurred on
    a given anniversary from the given date. For example, if the from date is
    April 2024 and the anniversaries are 1, 5, and 10 years, the selected
    records should be from April 2023, April 2019, and April 2013."""

    month, year = from_date.month, from_date.year

    # Index the archive records by month-year.
    month_year_records = {}
    for archive_record in archive_records:
        month_year = (int(archive_record["month"]), int(archive_record["year"]))
        if month_year not in month_year_records:
            month_year_records[month_year] = []
        month_year_records[month_year].append(archive_record)

    history_records = {}
    for num_years in anniversaries:
        anni_year = year - num_years
        try:
            # For each anniversary, get the entries for the archive for that
            # month and year.
            history_records[num_years] = month_year_records[(month, anni_year)]
        except KeyError:
            anni_date = datetime(anni_year, month, 1)
            anni_month_year_str = anni_date.strftime("%B %Y")
            err(
                f"Warning: No historical entries found for {anni_month_year_str}. Your local copy of the Top 10 Pony Videos master archive ({local_top_10_archive_csv_path}) may be out of date."
            )

    return history_records
