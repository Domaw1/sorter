import csv

def write_report(rows, filename="report.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["a", "b", "c"])
        writer.writerows(rows)
