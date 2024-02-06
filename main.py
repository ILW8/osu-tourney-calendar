import csv
import argparse
import datetime
import uuid

import dateutil.parser


def main(acronym: str, input_filename: str, skip_rows: int, id_column:int, date_column: int, time_column: int):
    with open(input_filename, 'r') as infile:
        file_data = infile.read()
    reader = csv.reader(file_data.splitlines())
    for _ in range(skip_rows):
        next(reader)

    ics_string = """BEGIN:VCALENDAR
CALSCALE:GREGORIAN
VERSION:2.0
METHOD:PUBLISH
PRODID:-//Apple Inc.//macOS 14.1.2//EN
"""
    cutoff_threshold = datetime.datetime.now(tz=datetime.timezone.utc)
    for row in reader:
        if row[id_column] == "":
            break
        date_time_str: str = f"{row[date_column]} {row[time_column]} UTC" \
            if date_column != time_column else f"{row[date_column]} UTC"

        match_id = row[id_column]
        match_datetime = dateutil.parser.parse(date_time_str, fuzzy=True)
        if match_datetime < cutoff_threshold:
            continue
        print(f"{acronym}: {match_id} @ {match_datetime}")
        ics_string += "BEGIN:VEVENT\n"
        ics_string += f"DTSTART:{match_datetime.strftime('%Y%m%dT%H%M%SZ')}\n"  # 20201124T123456Z
        ics_string += f"DTEND:{(match_datetime + datetime.timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}\n"

        dtstamp_now = datetime.datetime.now(tz=datetime.timezone.utc)
        ics_string += f"DTSTAMP:{dtstamp_now.strftime('%Y%m%dT%H%M%SZ')}\n"
        ics_string += f"SEQUENCE:{dtstamp_now.strftime('%Y%m%dT%H%M%SZ')}\n"
        ics_string += "STATUS:CONFIRMED\n"
        ics_string += f"SUMMARY:{acronym}: {match_id}\n"
        ics_string += f"UID:{uuid.uuid4()}\n"
        ics_string += "CLASS:PUBLIC\n"
        ics_string += "TRANSP:OPAQUE\n"
        ics_string += "END:VEVENT\n"
    ics_string += "END:VCALENDAR"
    with open(f"{acronym}_{datetime.datetime.now(tz=datetime.timezone.utc).timestamp()}.ics", "w") as outfile:
        outfile.write(ics_string)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("acronym", help="Tournament acronym", type=str)
    parser.add_argument("input", help="filename of a csv file containing match dates", type=str)
    parser.add_argument("skip_rows", help="how many rows to skip", type=int)
    parser.add_argument("--date_same_col_as_time",
                        help="whether date and time are in same column", action=argparse.BooleanOptionalAction)
    parser.add_argument("id_column", help="column containing match id", type=int)
    parser.add_argument("date_column", help="column containing date", type=int)
    parser.add_argument("--time_column", help="column containing time", type=int, required=False)
    args = parser.parse_args()

    # if args.prox and (args.lport is None or args.rport is None):
    #     parser.error("--prox requires --lport and --rport.")
    if args.date_same_col_as_time:
        if (args.date_column is not None and args.time_column is not None) and args.date_column != args.time_column:
            parser.error("date_same_col_as_time is true but date column and time column are not the same")
        the_col = args.date_column or args.time_column
        args.date_column = the_col
        args.time_column = the_col
    else:
        if args.time_column is None:
            parser.error("--time_column must be provided when --date_same_col_as_time is false")
    main(args.acronym, args.input, args.skip_rows, args.id_column, args.date_column, args.time_column)
