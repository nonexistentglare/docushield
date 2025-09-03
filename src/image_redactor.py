from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFilter
from pyzbar.pyzbar import decode

def detect_and_redact_qr(img: Image.Image) -> Tuple[Image.Image, List[Tuple[int,int,int,int]]]:
    barcodes = decode(img)
    boxes = []
    out_img = img.copy()
    draw = ImageDraw.Draw(out_img)
    for b in barcodes:
        x, y, w, h = b.rect
        draw.rectangle([x, y, x+w, y+h], fill="black")
        boxes.append((x, y, x+w, y+h))
    return out_img, boxes

def redact_on_image(img: Image.Image, boxes: List[Tuple[int,int,int,int]], style="black") -> Tuple[Image.Image, List[Tuple[int,int,int,int]]]:
    out = img.copy()
    draw = ImageDraw.Draw(out)
    applied = []
    for x0, y0, x1, y1 in boxes:
        if style == "black":
            draw.rectangle([x0, y0, x1, y1], fill="black")
        else:  # blur
            region = out.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(6))
            out.paste(region, (x0, y0))
        applied.append((x0, y0, x1, y1))
    return out, applied
