from app.export.html_report import render_html_report


def generate_pdf_report(report_data: dict) -> bytes:
    html = render_html_report(report_data)
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except ImportError:
        raise RuntimeError("WeasyPrint not installed. Install with: pip install weasyprint")
