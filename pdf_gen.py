import pdfkit
import io
import pandas as pd
from flask import send_file

def generate_pdf(x_axis, y_axis, graph_type, contents):
    # Prepare HTML content for the PDF
    content_html = f"""
    <h1>Dataset Analysis</h1>
    <p>Selected X-axis: {x_axis}</p>
    <p>Selected Y-axis: {y_axis}</p>
    <p>Graph Type: {graph_type}</p>
    """
    
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        content_html += f"<h2>Data Preview</h2><pre>{df.head().to_html()}</pre>"

    # Generate PDF
    pdf = pdfkit.from_string(content_html, False)

    # Return as BytesIO
    return io.BytesIO(pdf)

def download_pdf_file(pdf_bytes, filename):
    # Create a BytesIO buffer to hold the PDF
    pdf_bytes.seek(0)
    return send_file(pdf_bytes, as_attachment=True, download_name=filename, mimetype='application/pdf')
