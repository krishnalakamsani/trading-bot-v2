from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF


def _find_font(paths: list[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find a Unicode TTF font (DejaVu).")


def md_to_pdf(md_path: Path, pdf_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")

    dejavu_sans = _find_font(
        [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"),
        ]
    )
    dejavu_mono = _find_font(
        [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        ]
    )

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=14, top=14, right=14)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.add_font("DejaVu", style="", fname=str(dejavu_sans))
    pdf.add_font("DejaVu", style="B", fname=str(dejavu_sans))
    pdf.add_font("DejaVuMono", style="", fname=str(dejavu_mono))

    # Basic layout
    pdf.set_font("DejaVu", size=11)

    in_code_block = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                pdf.ln(1)
                pdf.set_font("DejaVuMono", size=9)
                pdf.set_text_color(30, 30, 30)
            else:
                pdf.set_font("DejaVu", size=11)
                pdf.ln(2)
            continue

        if in_code_block:
            # Preserve indentation; replace tabs for consistent rendering
            code_line = line.replace("\t", "    ")
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 4.2, code_line)
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            size = {1: 18, 2: 15, 3: 13, 4: 12, 5: 11, 6: 11}.get(level, 11)
            pdf.ln(2)
            pdf.set_font("DejaVu", style="B", size=size)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, title)
            pdf.set_font("DejaVu", size=11)
            pdf.ln(1)
            continue

        # Horizontal rule
        if line.strip() in {"---", "***", "___"}:
            pdf.ln(2)
            y = pdf.get_y()
            pdf.set_draw_color(200, 200, 200)
            pdf.line(14, y, 196, y)
            pdf.ln(3)
            continue

        # Bullets
        bullet_match = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if bullet_match:
            item = bullet_match.group(1)
            pdf.set_font("DejaVu", size=11)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5.2, f"• {item}")
            continue

        # Normal paragraph
        if line.strip() == "":
            pdf.ln(2)
            continue

        # Strip a couple of Markdown emphasis markers for readability
        clean = line
        clean = clean.replace("**", "")
        clean = clean.replace("__", "")
        clean = clean.replace("*", "")
        clean = clean.replace("`", "")

        pdf.set_font("DejaVu", size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5.2, clean)

    pdf.output(str(pdf_path))


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    md = root / "ARCHITECTURE_REPORT.md"
    out = root / "ARCHITECTURE_REPORT.pdf"
    md_to_pdf(md, out)
    print(f"Wrote: {out}")
