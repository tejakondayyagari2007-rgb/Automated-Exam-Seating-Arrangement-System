import csv
import io


def parse_csv_text(file_content):
    text_stream = io.StringIO(file_content.decode("utf-8-sig") if isinstance(file_content, bytes) else file_content)
    reader = csv.DictReader(text_stream)
    return list(reader)


def export_csv(rows, fieldnames):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()
