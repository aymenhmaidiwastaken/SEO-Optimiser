import re
from app.fixers.base import make_fix


def generate_image_fixes(pages) -> list[dict]:
    fixes = []
    for page in pages:
        missing_alt = [img for img in page.images if img.get("alt") is None]
        for img in missing_alt:
            src = img.get("src", "")
            # Generate alt text from filename
            filename = src.split("/")[-1].split("?")[0]
            # Remove extension and clean
            name = re.sub(r'\.[^.]+$', '', filename)
            name = re.sub(r'[-_]', ' ', name)
            name = re.sub(r'\d{5,}', '', name)  # Remove long numbers
            name = name.strip().title() or "Image"

            fixes.append(make_fix(
                "image_alt",
                f"Add alt text to image",
                f'<img src="{src}" alt="{name}">',
                page_url=page.url,
                original=f'<img src="{src}">',
            ))

    return fixes
