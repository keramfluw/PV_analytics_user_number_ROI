import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
from cycler import cycler
from PIL import Image
import io
import os

# Optional: PDF-Export
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# Unternehmensdaten / Footer
COMPANY_BLOCK = """Qrauts AG
Oltmannstraße 34
79100 Freiburg im Breisgau
Deutschland

Telefon: 07761 5090 281
E-Mail: info@qrauts.de
Webseite: www.qrauts.de

Ansprechpartner und Autor der Webanwendung:
Herr Marek Wulff (Vorstand Operativ I COO)
Registergericht: Amtsgericht Freiburg im Breisgau
Handelsregisternummer: HRB 732712
Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: DE452526002
"""

# Branding & Assets
PRIMARY = "#F37021"
PRIMARY_DARK = "#D85C16"
ACCENT = "#FFAE6D"
TEXT = "#111111"
BG = "#FFF8F2"
SIDEBAR_BG = "#FFF3E6"

# Fixed asset directory path
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
DEFAULT_LOGO_FILE = "qrauts_logo.png"

def load_logo():
    # Try assets directory first
    assets_logo_path = os.path.join(ASSETS_DIR, DEFAULT_LOGO_FILE)
    if os.path.exists(assets_logo_path):
        return Image.open(assets_logo_path)
    # Try fallback container path
    default_path = "/mnt/data/Bild 15.08.25 um 18.24.png"
    if os.path.exists(default_path):
        return Image.open(default_path)
    # Allow upload as last resort
    uploaded = st.sidebar.file_uploader("Optional: eigenes Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        bytes_data = uploaded.read()
        return Image.open(io.BytesIO(bytes_data))
    return None

logo_img = load_logo()

st.set_page_config(
    page_title="PV-Projekt-Kalkulation",
    layout="wide",
    page_icon=logo_img if logo_img else "☀️"
)

# (The rest of your Streamlit app code would follow here...)
