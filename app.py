from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import qrcode
from io import BytesIO
from pathlib import Path
import json, threading, webbrowser

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "videos.json"
app = Flask(__name__)

def load_videos():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

@app.route("/")
def index():
    cats = {}
    for v in load_videos():
        cats.setdefault(v["category"], []).append(v)
    return render_template("index.html", categories=cats)

@app.post("/generate")
def generate():
    ids = request.form.getlist("video_ids")
    selected = [v for v in load_videos() if v["id"] in ids]
    if not selected:
        return "Please select at least one video.", 400

    out = BytesIO()
    c = canvas.Canvas(out, pagesize=letter)
    pw, ph = letter
    cols, rows = 2, 3
    mx, my = .55*inch, .55*inch
    cw = (pw - 2*mx)/cols
    ch = (ph - 2*my)/rows
    qr_size = 1.72*inch

    for i, v in enumerate(selected):
        pos = i % 6
        if pos == 0 and i:
            c.showPage()
        col, row = pos % 2, pos // 2
        x = mx + col*cw
        y = ph - my - (row+1)*ch

        c.setFont("Helvetica-Bold", 12)
        title = v["title"] if len(v["title"]) <= 34 else v["title"][:31] + "..."
        c.drawCentredString(x+cw/2, y+ch-.28*inch, title)

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=10, border=2)
        qr.add_data(v["url"]); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        qx = x+(cw-qr_size)/2
        qy = y+(ch-qr_size)/2-.04*inch
        c.drawImage(ImageReader(buf), qx, qy, qr_size, qr_size)

        c.setFont("Helvetica", 8)
        c.drawCentredString(x+cw/2, y+.17*inch, "Scan to watch video")
    c.save(); out.seek(0)
    return send_file(out, mimetype="application/pdf", as_attachment=True,
                     download_name="REACH_Video_QR_Codes.pdf")

if __name__ == "__main__":
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
