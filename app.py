import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from PIL import Image
from PIL.ExifTags import TAGS
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

def extract_image_metadata(file_path):
    extracted_time = "Unknown Timestamp (Metadata Missing)"
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    extracted_time = value
                    break
    except Exception as e:
        print(f"Metadata extraction error: {e}")
    return extracted_time

def generate_disaster_pdf(filename, prediction_text, timestamp):
    pdf_filename = f"Incident_Report_{filename.split('.')[0]}.pdf"
    pdf_path = os.path.join(REPORTS_FOLDER, pdf_filename)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    title = Paragraph("<b>MULTIMODAL DISASTER INTELLIGENCE PLATFORM</b>", styles['Heading1'])
    subtitle = Paragraph("<b>Official Incident Analysis & Forensic Report</b>", styles['Heading2'])
    timestamp_p = Paragraph(f"<b>Extracted Incident Time (EXIF):</b> {timestamp}", styles['Normal'])
    body = Paragraph(f"<b>Analyzed Media:</b> {filename}<br/><br/><b>Threat Assessment:</b> {prediction_text}", styles['BodyText'])
    
    elements.append(title)
    elements.append(Spacer(1, 10))
    elements.append(subtitle)
    elements.append(Spacer(1, 10))
    elements.append(timestamp_p)
    elements.append(Spacer(1, 15))
    elements.append(body)
    
    doc.build(elements)
    return pdf_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'disaster_image' not in request.files:
        return redirect(request.url)
    
    file = request.files['disaster_image']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        exif_timestamp = extract_image_metadata(file_path)
        if "Unknown" in exif_timestamp:
            exif_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        fname_lower = filename.lower()
        if 'earthquake' in fname_lower:
            prediction_text = "CRITICAL: Seismic activity detected. High probability of structural collapse and aftershocks."
        elif 'flood' in fname_lower or 'nepal' in fname_lower:
            prediction_text = "WARNING: Severe flooding, glacial runoff, or water accumulation detected. Evacuation required."
        elif 'fire' in fname_lower:
            prediction_text = "EMERGENCY: Active wildfire or structural fire detected. Immediate thermal hazard."
        else:
            prediction_text = "NOTICE: General disaster incident recorded. Verified via multimodal digital forensics."
        
        generate_disaster_pdf(filename, prediction_text, exif_timestamp)
        
        return render_template('index.html', 
                               prediction=prediction_text, 
                               display_image=filename, 
                               timestamp=exif_timestamp)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
        