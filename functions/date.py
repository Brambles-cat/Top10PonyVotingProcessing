"""General functions for dealing with awkward dates and durations."""

import re
from datetime import datetime
from pytz import timezone
from functions.general import get_freq_table
from classes.voting import Ballot


def parse_votes_csv_timestamp(timestamp: str) -> datetime:
    """Parse the timestamp from the votes CSV file into a datetime object.

    The timestamp is in the format M/D/Y h:m:s, where - annoyingly - M, D, and h
    can have either 1 or 2 digits. Python's `strptime` parser isn't able to
    handle that, so we have to preprocess the date a little first.
    """

    timestamp = timestamp.strip()
    pattern = r"^(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)$"
    match = re.match(pattern, timestamp)
    try:
        date_components = match.groups()
    except AttributeError:
        raise ValueError(
            f'Cannot parse votes CSV timestamp "{timestamp}"; invalid format'
        )

    if len(date_components) != 6:
        raise ValueError(
            f'Cannot parse votes CSV timestamp "{timestamp}"; invalid format'
        )

    month, day, year, hour, minute, second = date_components
    month = month.zfill(2)
    day = day.zfill(2)
    year = year.zfill(4)
    hour = hour.zfill(2)
    minute = minute.zfill(2)
    second = second.zfill(2)

    processed_timestamp = f"{month}/{day}/{year} {hour}:{minute}:{second}"

    timestamp_format = "%m/%d/%Y %H:%M:%S"
    dt = datetime.strptime(processed_timestamp, timestamp_format)

    return dt.replace(tzinfo=None)


def format_votes_csv_timestamp(dt: datetime) -> str:
    """Format a datetime into the timestamp format used by the votes CSV
    (M/D/Y h:m:s)
    """
    month = dt.month
    day = dt.day
    year = dt.year
    hour = dt.hour
    minute = str(dt.minute).zfill(2)
    second = str(dt.second).zfill(2)
    return f"{month}/{day}/{year} {hour}:{minute}:{second}"


def convert_iso8601_duration_to_seconds(iso8601_duration: str) -> int:
    """Given an ISO 8601 duration string, return the length of that duration in
    seconds.

    Note: Apparently the isodate package can perform this conversion if needed.
    """
    if iso8601_duration.startswith("PT"):
        iso8601_duration = iso8601_duration[2:]

    total_seconds, hours, minutes, seconds = 0, 0, 0, 0

    if "H" in iso8601_duration:
        hours_part, iso8601_duration = iso8601_duration.split("H")
        hours = int(hours_part)

    if "M" in iso8601_duration:
        minutes_part, iso8601_duration = iso8601_duration.split("M")
        minutes = int(minutes_part)

    if "S" in iso8601_duration:
        seconds_part = iso8601_duration.replace("S", "")
        seconds = int(seconds_part)

    total_seconds = hours * 3600 + minutes * 60 + seconds

    return total_seconds


def get_preceding_month_date(date: datetime) -> datetime:
    """Given a date, return the date corresponding to the first day of the
    preceding month.
    """
    preceding_month = date.month - 1 if date.month > 1 else 12
    preceding_year = date.year if date.month > 1 else date.year - 1
    return datetime(preceding_year, preceding_month, 1, tzinfo=date.tzinfo)


def get_month_year_bounds(
    month: int, year: int, lenient=False
) -> tuple[datetime, datetime]:
    """Given a month and year, return the two dates that bound that month (ie.
    the first day of the month, and the first day of the next month). If lenient
    is true, then the lower and upper date bounds will use the most lenient
    timezones possible."""

    lower_timezone = None
    upper_timezone = None

    # If leniency is requested, use the following timezones for the lower and
    # upper date bounds:
    # * Lower: Kiribati, UTC+14:00
    # * Upper: International Date Line West (IDLW), UTC:-12:00
    if lenient:
        lower_timezone = timezone("Etc/GMT-14")
        upper_timezone = timezone("Etc/GMT+12")

    lower_bound = datetime(year, month, 1, tzinfo=lower_timezone)
    upper_bound = None
    if month < 12:
        upper_bound = lower_bound.replace(
            month=lower_bound.month + 1, tzinfo=upper_timezone
        )
    else:
        upper_bound = lower_bound.replace(
            year=lower_bound.year + 1, month=1, tzinfo=upper_timezone
        )

    return lower_bound, upper_bound


def is_date_between(
    date: datetime, lower_bound: datetime, upper_bound: datetime
) -> bool:
    """Return True if the given date is between the given bounds."""
    return date >= lower_bound and date < upper_bound


def guess_voting_month_year(ballots: list[Ballot]) -> tuple[int, int, bool]:
    """Given a list of ballots, attempt to determine what month and year the
    votes are being cast in. This uses a simple heuristic of counting the most
    common month-year in the ballot timestamps.

    Remember that votes are cast in the month after the videos are uploaded, so
    if the voting month year is April 2024, the videos were uploaded in March
    2024 (and would be featured in the "Top 10 Pony Videos of March 2024"
    showcase).

    Returns a tuple of 3 values: month, year, and is_unanimous, which is set to
    True if all ballots agreed on the same month and year."""

    ballot_timestamps = [ballot.timestamp for ballot in ballots]
    return get_most_common_month_year(ballot_timestamps)


def get_most_common_month_year(dates: list[datetime]) -> tuple[int, int, bool]:
    """Given a list of dates, return the most common month and year among
    them.

    Returns a tuple of 3 values: month, year, and is_unanimous, which is set to
    True if all dates agree on the same month and year."""
    month_years = [(date.month, date.year) for date in dates]
    month_year_counts = get_freq_table(month_years)

    sorted_month_years = sorted(
        month_year_counts,
        key=lambda my: month_year_counts[my],
        reverse=True,
    )

    most_common_month_year = sorted_month_years[0]
    is_unanimous = len(sorted_month_years) == 1

    return (*most_common_month_year, is_unanimous)


def rel_anni_date_to_abs(rel_date: str, from_date: datetime) -> datetime:
    """Given a date of the relative form "N years ago", and an absolute from
    date, return the date in absolute form. For example, if the date is "5 years
    ago" and the from date is 2024-04-01, the result should be 2019-04-01."""

    rel_date_words = rel_date.split(' ')
    if len(rel_date_words) != 3:
        raise ValueError(f'Cannot convert relative date "{rel_date}" to absolute date; date must be given in form "N year ago" or "N years ago"')

    years_ago = None
    try:
        years_ago = int(rel_date_words[0])
    except ValueError as error:
        raise ValueError(f'Cannot convert relative date "{rel_date}" to absolute date; first word of relative date must be an integer number of years"') from error

    if ' '.join(rel_date_words[1:]) not in ['year ago', 'years ago']:
        raise ValueError(f'Cannot convert relative date "{rel_date}" to absolute date; date must end in "year ago" or "years ago""')

    abs_date = from_date.replace(year=from_date.year - years_ago) 

    return abs_date
