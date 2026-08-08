from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from openpyxl import Workbook
import csv

def build_report(report_type: str, output: Path, title: str, rows: list[dict]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if report_type == "pdf":
        doc = SimpleDocTemplate(str(output), pagesize=A4); styles = getSampleStyleSheet(); story = [Paragraph(title, styles["Title"]), Spacer(1, 16)]
        for row in rows:
            story.append(Paragraph("<br/>".join(f"<b>{key.replace('_', ' ').title()}:</b> {value}" for key, value in row.items()), styles["BodyText"])); story.append(Spacer(1, 10))
        doc.build(story); return
    if report_type == "xlsx":
        workbook = Workbook(); sheet = workbook.active; sheet.title = "Farm report"
        headers = sorted({key for row in rows for key in row}) or ["message"]; sheet.append(headers)
        for row in rows: sheet.append([str(row.get(header, "")) for header in headers])
        workbook.save(output); return
    with output.open("w", newline="", encoding="utf-8") as file:
        headers = sorted({key for row in rows for key in row}) or ["message"]; writer = csv.DictWriter(file, fieldnames=headers); writer.writeheader(); writer.writerows(rows)
