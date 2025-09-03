import os
from pathlib import Path
from typing import List, Dict, Tuple
import click
from PIL import Image
import fitz

from pii_patterns import get_rules
from ocr_utils import ocr_words
from image_redactor import redact_on_image, detect_and_redact_qr
from pdf_utils import page_to_image, redact_boxes_on_page
from audit import write_audit

SUPPORTED_IMG = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

def gather_files(input_path: Path, extensions: List[str]) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    exts = {e.lower().strip() for e in extensions}
    return [p for p in input_path.rglob("*") if p.suffix.lower() in exts]

def match_pii(tokens: List[Dict], rules: List[Tuple[str, object]], min_conf:int):
    boxes = []
    reasons = []

    # Detect token-wise
    for w in tokens:
        if w["conf"] < min_conf:
            continue
        for label, rx in rules:
            if rx.search(w["text"]):
                x0, y0 = w["left"], w["top"]
                x1, y1 = x0 + w["width"], y0 + w["height"]
                boxes.append((x0, y0, x1, y1))
                reasons.append({"label":label, "text":w["text"], "conf":w["conf"], "bbox":[x0,y0,x1,y1]})
                break

    # Line-wise aggregation for multi-token PII as needed
    lines = {}
    for w in tokens:
        key = int(round(w["top"] / 10))
        lines.setdefault(key, []).append(w)
    for ws in lines.values():
        ws_sorted = sorted(ws, key=lambda x: x["left"])
        line_text = " ".join(t["text"] for t in ws_sorted)
        for label, rx in rules:
            if rx.search(line_text):
                x0 = min(t["left"] for t in ws_sorted)
                x1 = max(t["left"]+t["width"] for t in ws_sorted)
                y0 = min(t["top"] for t in ws_sorted)
                y1 = max(t["top"]+t["height"] for t in ws_sorted)
                boxes.append((x0, y0, x1, y1))
                reasons.append({"label":label, "text":line_text, "conf": max(t["conf"] for t in ws_sorted), "bbox":[x0,y0,x1,y1]})
                break

    return boxes, reasons

def process_image(img_path: Path, out_dir: Path, style: str, lang: str, min_conf: int, fields: List[str]):
    img = Image.open(img_path).convert("RGB")

    # QR code redaction
    img, qr_boxes = detect_and_redact_qr(img)

    tokens = ocr_words(img, lang=lang)
    rules = get_rules(fields)
    boxes, reasons = match_pii(tokens, rules, min_conf)

    # Include QR boxes in redaction
    all_boxes = boxes + qr_boxes
    redacted_img, _ = redact_on_image(img, all_boxes, style=style)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_img = out_dir / f"{img_path.stem}_redacted{img_path.suffix}"
    redacted_img.save(out_img)

    audit = {
        "input": str(img_path),
        "output": str(out_img),
        "type": "image",
        "detections": reasons,
        "qr_redacted": len(qr_boxes),
        "fields_redacted": fields,
    }
    write_audit(audit, out_dir / f"{img_path.stem}_audit.json")

def process_pdf(pdf_path: Path, out_dir: Path, style: str, lang: str, min_conf: int, fields: List[str], dpi: int=200):
    doc = fitz.open(pdf_path)
    per_page = []
    rules = get_rules(fields)

    for i in range(len(doc)):
        img, sx, sy = page_to_image(doc, i, dpi=dpi)

        img, qr_boxes = detect_and_redact_qr(img)
        tokens = ocr_words(img, lang=lang)
        boxes, reasons = match_pii(tokens, rules, min_conf)
        all_boxes = boxes + qr_boxes
        boxes_pdf = [(x0/sx, y0/sy, x1/sx, y1/sy) for (x0,y0,x1,y1) in all_boxes]

        page = doc.load_page(i)
        if boxes_pdf:
            redact_boxes_on_page(page, boxes_pdf)

        per_page.append({"page": i+1, "detections": reasons, "qr_redacted": len(qr_boxes)})

    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = out_dir / f"{pdf_path.stem}_redacted.pdf"
    doc.save(out_pdf)
    doc.close()

    audit = {
        "input": str(pdf_path),
        "output": str(out_pdf),
        "type": "pdf",
        "pages": per_page,
        "fields_redacted": fields,
    }
    write_audit(audit, out_dir / f"{pdf_path.stem}_audit.json")

@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=Path("out"))
@click.option("--style", type=click.Choice(["black","blur"]), default="black")
@click.option("--lang", type=str, default="eng+hin")
@click.option("--min-conf", type=int, default=60)
@click.option("--fields", type=str, default="AADHAAR,PAN,PHONE,EMAIL,DATE")
@click.option("--extensions", type=str, default=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp")
@click.option("--dpi", type=int, default=200)
def main(input_path: Path, out_dir: Path, style: str, lang: str, min_conf: int, fields: str, extensions: str, dpi: int):
    selected_fields = [f.strip().upper() for f in fields.split(",")]
    files = gather_files(input_path, extensions.split(","))
    for f in files:
        if f.suffix.lower() == ".pdf":
            process_pdf(f, out_dir, style, lang, min_conf, selected_fields, dpi)
        elif f.suffix.lower() in SUPPORTED_IMG:
            process_image(f, out_dir, style, lang, min_conf, selected_fields)
        else:
            print(f"[yellow]Skipping unsupported file: {f}[/yellow]")

if __name__ == "__main__":
    main()
