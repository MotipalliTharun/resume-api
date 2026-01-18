from weasyprint import HTML

async def html_to_pdf(html: str) -> bytes:
    """
    Convert HTML string to PDF using WeasyPrint (Headless, no container needed).
    """
    return HTML(string=html).write_pdf()

async def text_to_pdf(text: str) -> bytes:
    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: sans-serif; line-height: 1.4; font-size: 12px; }}
          pre {{ white-space: pre-wrap; }}
        </style>
      </head>
      <body>
        <pre>{text}</pre>
      </body>
    </html>
    """
    return await html_to_pdf(html)
