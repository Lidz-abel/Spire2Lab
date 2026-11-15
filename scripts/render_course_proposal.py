"""Render the standalone, offline Proposal HTML to a checked two-page A4 PDF.

Uses system Pango/Cairo with no browser, service or dependency installation.
No project/game modules are imported. Run with the system python3.
Identity is applied only to generated private artifacts, not tracked HTML.
"""

import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess
import zipfile

from course_pdf_layout import Document, Renderer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name")
    parser.add_argument("--student-id")
    args = parser.parse_args()
    if bool(args.name) != bool(args.student_id):
        parser.error("Provide both --name and --student-id, or neither.")
    if args.student_id and not re.fullmatch(r"[A-Za-z0-9_-]+", args.student_id):
        parser.error("Student ID must contain only letters, digits, underscores or hyphens.")

    source = Path(__file__).resolve().parents[1] / "docs/course/proposal.html"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    pdf = output / "proposal.pdf"
    identity_complete = bool(args.name and args.student_id)
    content = source.read_text(encoding="utf-8")
    if identity_complete:
        content = content.replace('<span id="student-name">待填写</span>', f'<span id="student-name">{escape(args.name)}</span>')
        content = content.replace('<span id="student-id">待填写</span>', f'<span id="student-id">{escape(args.student_id)}</span>')
    layout = Renderer(pdf).render(Document(content))
    (output / "proposal.html").write_text(content, encoding="utf-8")

    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
    if not match or int(match.group(1)) != 2:
        raise RuntimeError(f"Expected two PDF pages: {info}")
    subprocess.run(["pdftotext", "-layout", str(pdf), str(output / "proposal-extracted.txt")], check=True)
    extracted = (output / "proposal-extracted.txt").read_text(encoding="utf-8")
    for required in ["Spire2Lab", "强化学习", "11.16", "11.30", "12.21", "12.28", "PPO"]:
        if required not in extracted:
            raise RuntimeError(f"Missing required text in PDF: {required}")
    if identity_complete and "待填写" in extracted:
        raise RuntimeError("Identity placeholder remains in personalized PDF.")

    archive_name = f"{args.student_id}_proposal.zip" if identity_complete else "待填学号_proposal.zip"
    archive = output / archive_name
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(pdf, "proposal.pdf")
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None or bundle.namelist() != ["proposal.pdf"]:
            raise RuntimeError("Submission ZIP verification failed.")
    report = {
        "pdf": pdf.name,
        "pages": 2,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "zip": archive.name,
        "zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "identity_complete": identity_complete,
        "submitted": False,
        "renderer": "system Pango/Cairo; no browser or new dependency",
        "layout": layout,
        "scope": "document rendering and packaging only; no training or game validation",
    }
    (output / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
