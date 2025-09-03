from typing import List, Tuple
import fitz
from PIL import Image

def page_to_image(doc: fitz.Document, page_num: int, dpi: int=200) -> Tuple[Image.Image, float, float]:
    page = doc.load_page(page_num)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    mode = "RGB" if pix.n < 4 else "RGBA"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    return img, zoom, zoom

def redact_boxes_on_page(page: fitz.Page, boxes: List[Tuple[float, float, float, float]], fill=(0,0,0)):
    for box in boxes:
        page.add_redact_annot(fitz.Rect(*box), fill=fill)
    page.apply_redactions()
