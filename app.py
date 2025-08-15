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

# -----------------------
# Branding & Assets
# -----------------------
PRIMARY = "#F37021"       # Qrauts Orange
PRIMARY_DARK = "#D85C16"
ACCENT = "#FFAE6D"
TEXT = "#111111"
BG = "#FFF8F2"            # sehr helles Beige
SIDEBAR_BG = "#FFF3E6"

DEFAULT_LOGO_PATH = "/mnt/data/Bild 15.08.25 um 18.24.png"

def load_logo():
    if os.path.exists(DEFAULT_LOGO_PATH):
        return Image.open(DEFAULT_LOGO_PATH)
    uploaded = st.sidebar.file_uploader("Optional: eigenes Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        bytes_data = uploaded.read()
        return Image.open(io.BytesIO(bytes_data))
    return None

logo_img = load_logo()

# -----------------------
# Page & Theming
# -----------------------
st.set_page_config(
    page_title="PV-Projekt-Kalkulation",
    layout="wide",
    page_icon=logo_img if logo_img else "☀️"
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, {BG} 0%, #FFFFFF 100%);
        color: {TEXT};
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: {SIDEBAR_BG};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {PRIMARY_DARK} !important;
    }}
    .stMetric label {{
        color: {PRIMARY_DARK} !important;
    }}
    .stButton>button {{
        background-color: {PRIMARY};
        border: 0px;
        color: white;
        border-radius: 10px;
    }}
    .stButton>button:hover {{
        background-color: {PRIMARY_DARK};
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#DDDDDD",
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "text.color": TEXT,
    "grid.color": "#E6E6E6",
    "axes.prop_cycle": cycler(color=[PRIMARY, "#000000", PRIMARY_DARK, "#6C6C6C"])
})

# -----------------------
# Header mit Logo
# -----------------------
cols = st.columns([1, 5])
with cols[0]:
    if logo_img:
        st.image(logo_img, use_container_width=True)
with cols[1]:
    st.title("☀️ PV-Projekt-Kalkulation Dashboard V1.0 Qrauts AG")
    st.caption("simply different")

# -----------------------
# Eingabemaske
# -----------------------
st.sidebar.header("🔧 Eingabeparameter")

# Technisch-wirtschaftliche Parameter
size_kwp = st.sidebar.number_input("Anlagengröße (kWp)", min_value=1.0, value=100.0)
yield_kwh_kwp = st.sidebar.number_input("Spezifischer Ertrag (kWh/kWp)", min_value=500.0, value=950.0)
self_consumption_rate = st.sidebar.slider("Eigenverbrauchsanteil (%)", 0, 100, 60)
system_efficiency = st.sidebar.slider("Systemnutzungsgrad (%)", 50, 100, 90)
lifetime_years = st.sidebar.slider("Lebensdauer der Anlage (Jahre)", 10, 30, 25)

# Investitionskosten
capex_pv = st.sidebar.number_input("PV-Anlage (€)", min_value=0.0, value=100000.0)
capex_storage = st.sidebar.number_input("Speicher (€)", min_value=0.0, value=20000.0)
capex_other = st.sidebar.number_input("Weitere Kosten (€)", min_value=0.0, value=30000.0)
capex_total = capex_pv + capex_storage + capex_other

# Betriebskosten
opex_annual = st.sidebar.number_input("Jährliche Betriebskosten (€)", min_value=0.0, value=5000.0)

# Finanzierung
loan_share = st.sidebar.slider("Fremdkapitalanteil (%)", 0, 100, 70)
interest_rate = st.sidebar.slider("Kreditzins (%)", 0.0, 10.0, 3.0)
repayment_years = st.sidebar.slider("Tilgungsdauer (Jahre)", 1, 30, 20)

# Einnahmen
price_self_consumption = st.sidebar.number_input("Mieterstromerlös (ct/kWh)", min_value=0.0, value=25.0) / 100
price_feed_in = st.sidebar.number_input("Einspeisevergütung (ct/kWh)", min_value=0.0, value=8.0) / 100
inflation_rate = st.sidebar.slider("Strompreissteigerung (%)", 0.0, 10.0, 2.0) / 100

# Szenarien
scenarios = {
    "Bundesdurchschnitt": 1.0,
    "Optimistisch": 1.1,
    "Pessimistisch": 0.9
}

# -----------------------
# Berechnungen
# -----------------------
def calculate_cashflow(scenario_factor):
    annual_production = size_kwp * yield_kwh_kwp * system_efficiency / 100 * scenario_factor
    self_consumed = annual_production * self_consumption_rate / 100
    fed_into_grid = annual_production - self_consumed

    cashflows = []
    cumulative = []
    for year in range(1, lifetime_years + 1):
        price_self = price_self_consumption * ((1 + inflation_rate) ** (year - 1))
        price_feed = price_feed_in * ((1 + inflation_rate) ** (year - 1))
        revenue = self_consumed * price_self + fed_into_grid * price_feed
        cost = opex_annual
        net_cashflow = revenue - cost
        cashflows.append(net_cashflow)
        cumulative.append(sum(cashflows))

    return cashflows, cumulative

# -----------------------
# Charts: Szenarien & Break-even
# -----------------------
st.subheader("📊 Szenarienvergleich: Cashflow & Break-even")

fig, ax = plt.subplots(figsize=(10, 5))
for name, factor in scenarios.items():
    cf, cum_cf = calculate_cashflow(factor)
    ax.plot(range(1, lifetime_years + 1), cum_cf, label=name, linewidth=2)
    for i, val in enumerate(cum_cf):
        if val >= capex_total:
            ax.axvline(i + 1, linestyle='--', color="#9E9E9E", alpha=0.3)
            break

ax.axhline(capex_total, color=PRIMARY, linestyle=':', label='Investitionskosten', linewidth=2)
ax.set_xlabel("Jahr")
ax.set_ylabel("Kumulierter Cashflow (€)")
ax.set_title("Cashflow-Verlauf und Break-even")
ax.grid(True, linestyle=":", linewidth=0.7)
ax.legend()
st.pyplot(fig)

# -----------------------
# KPI-Dashboard
# -----------------------
st.subheader("📈 Projekt-Kennzahlen")

base_cf, base_cum = calculate_cashflow(1.0)
amort_year = next((i + 1 for i, val in enumerate(base_cum) if val >= capex_total), "nicht erreicht")
irr_estimate = npf.irr([-capex_total] + base_cf)
lcoe = capex_total / (size_kwp * yield_kwh_kwp * system_efficiency / 100 * lifetime_years)

col1, col2, col3 = st.columns(3)
col1.metric("Amortisationsjahr", amort_year)
col2.metric("geschätzte IRR-Interne Rendite", f"{irr_estimate:.2%}" if irr_estimate else "n/a")
col3.metric("LCOE-Stromgestehungskosten (€/kWh)", f"{lcoe:.4f}")

st.caption("Hinweis: Die Berechnungen basieren auf vereinfachten Annahmen und dienen der Projektbewertung. Autor: Marek Wulff")

# -----------------------
# Analyse: Strompreis vs. Nutzerquote
# -----------------------
st.header("📊 Analyse: Strompreis abhängig von PV-Nutzerquote")

min_quote = 10
max_quote = 100
step = 10
quotes = np.arange(min_quote, max_quote + 1, step)

annual_yield_total = size_kwp * yield_kwh_kwp * (system_efficiency / 100)

loan_amount = capex_total * (loan_share / 100)
equity_amount = capex_total - loan_amount
annuity = npf.pmt(interest_rate / 100, repayment_years, -loan_amount)
total_annual_costs = annuity + opex_annual

effective_prices = []
profits = []

for quote in quotes:
    user_share = quote / 100
    pv_for_users = annual_yield_total * (self_consumption_rate / 100) * user_share
    pv_feed_in = annual_yield_total - pv_for_users

    revenue_users = pv_for_users * price_self_consumption
    revenue_feed_in = pv_feed_in * price_feed_in
    total_revenue = revenue_users + revenue_feed_in

    profit = total_revenue - total_annual_costs

    if pv_for_users > 0:
        price_per_kwh = (total_annual_costs - revenue_feed_in) / pv_for_users
    else:
        price_per_kwh = np.nan

    effective_prices.append(price_per_kwh)
    profits.append(profit)

# Plot: Effektiver Mieterstrompreis
fig1, ax1 = plt.subplots()
ax1.plot(quotes, np.array(effective_prices)*100, marker="o", linewidth=2,
         label="Effektiver Mieterstrompreis (ct/kWh)")
for x, y in zip(quotes, np.array(effective_prices)*100):
    ax1.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8)
ax1.set_xlabel("PV-Nutzerquote (%)")
ax1.set_ylabel("Preis (ct/kWh)")
ax1.set_title("Effektiver Mieterstrompreis je nach Nutzerquote")
ax1.grid(True, linestyle=":", linewidth=0.7)
ax1.legend()
st.pyplot(fig1)

# Plot: Gewinn
fig2, ax2 = plt.subplots()
ax2.plot(quotes, profits, marker="s", linewidth=2, label="Jährlicher Gewinn (€)")
for x, y in zip(quotes, profits):
    ax2.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8)
ax2.set_xlabel("PV-Nutzerquote (%)")
ax2.set_ylabel("Jährlicher Gewinn (€)")
ax2.set_title("Wirtschaftlichkeit der PV-Anlage je nach Nutzerquote")
ax2.grid(True, linestyle=":", linewidth=0.7)
ax2.legend()
st.pyplot(fig2)

# Footer-Logo in der Sidebar
st.sidebar.markdown("---")
if logo_img:
    st.sidebar.image(logo_img, caption="Qrauts – simply different", use_container_width=True)

# =========================================================
# ============== EXPORT: EXCEL & PDF ======================
# =========================================================

def build_excel_bytes():
    """Erzeugt eine Excel-Arbeitsmappe mit mehreren Sheets und gibt BytesIO zurück."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Parameter
        params = pd.DataFrame({
            "Parameter": [
                "Anlagengröße (kWp)", "Spez. Ertrag (kWh/kWp)", "Eigenverbrauch (%)",
                "Systemnutzungsgrad (%)", "Lebensdauer (Jahre)",
                "CAPEX PV (€)", "CAPEX Speicher (€)", "CAPEX Sonstiges (€)", "CAPEX total (€)",
                "OPEX p.a. (€)", "FK-Anteil (%)", "Zins (%)", "Tilgungsdauer (J)",
                "Mieterstromerlös (€/kWh)", "Einspeisevergütung (€/kWh)", "Preissteigerung (%)"
            ],
            "Wert": [
                size_kwp, yield_kwh_kwp, self_consumption_rate,
                system_efficiency, lifetime_years,
                capex_pv, capex_storage, capex_other, capex_total,
                opex_annual, loan_share, interest_rate, repayment_years,
                price_self_consumption, price_feed_in, inflation_rate
            ]
        })
        params.to_excel(writer, sheet_name="Parameter", index=False)

        # KPI
        kpi = pd.DataFrame({
            "Kennzahl": ["Amortisationsjahr", "IRR", "LCOE (€/kWh)"],
            "Wert": [amort_year, float(irr_estimate) if irr_estimate is not None else np.nan, lcoe]
        })
        kpi.to_excel(writer, sheet_name="KPI", index=False)

        # Cashflow Szenarien
        years = list(range(1, lifetime_years + 1))
        cf_df = pd.DataFrame({"Jahr": years})
        cum_df = pd.DataFrame({"Jahr": years})
        for name, factor in scenarios.items():
            cf, cum = calculate_cashflow(factor)
            cf_df[name] = cf
            cum_df[name] = cum
        cf_df.to_excel(writer, sheet_name="Cashflow je Jahr", index=False)
        cum_df.to_excel(writer, sheet_name="Kumuliert", index=False)

        # Nutzerquote-Analyse
        nq = pd.DataFrame({
            "Nutzerquote_%": quotes,
            "Effektiver_Preis_ct/kWh": np.array(effective_prices) * 100,
            "Gewinn_€": profits
        })
        nq.to_excel(writer, sheet_name="Nutzerquote-Analyse", index=False)

        # Formate minimal setzen
        workbook  = writer.book
        for ws_name in ["Parameter", "KPI", "Cashflow je Jahr", "Kumuliert", "Nutzerquote-Analyse"]:
            try:
                ws = writer.sheets[ws_name]
                ws.set_tab_color("#F37021")
            except Exception:
                pass

    output.seek(0)
    return output

def build_pdf_bytes():
    """Erzeugt einen kompakten PDF-Bericht inkl. Diagrammen. Erfordert reportlab."""
    if not REPORTLAB_AVAILABLE:
        return None

    # Figuren als PNG in Memory speichern
    buf_fig = io.BytesIO()
    fig.savefig(buf_fig, format="png", bbox_inches="tight", dpi=180)
    buf_fig.seek(0)

    buf_fig1 = io.BytesIO()
    fig1.savefig(buf_fig1, format="png", bbox_inches="tight", dpi=180)
    buf_fig1.seek(0)

    buf_fig2 = io.BytesIO()
    fig2.savefig(buf_fig2, format="png", bbox_inches="tight", dpi=180)
    buf_fig2.seek(0)

    # PDF bauen
    pdf_bytes = io.BytesIO()
    c = canvas.Canvas(pdf_bytes, pagesize=A4)
    width, height = A4
    margin = 36  # 0.5 inch

    # Header
    y = height - margin
    if logo_img:
        # logo auf max Breite 120px begrenzen
        logo_buf = io.BytesIO()
        logo_img.save(logo_buf, format="PNG")
        logo_buf.seek(0)
        c.drawImage(ImageReader(logo_buf), margin, y-40, width=120, preserveAspectRatio=True, mask='auto')
    c.setFillColor(colors.HexColor(PRIMARY_DARK))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin+130, y-20, "PV-Projekt – Ergebnisbericht")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    y -= 60
    c.drawString(margin, y, "Parameter & Eckdaten:")
    y -= 12

    # Parameter-Block (2 Spalten)
    left = [
        f"Anlagengröße: {size_kwp} kWp",
        f"Spez. Ertrag: {yield_kwh_kwp} kWh/kWp",
        f"Eigenverbrauch: {self_consumption_rate} %",
        f"Systemnutzungsgrad: {system_efficiency} %",
        f"Lebensdauer: {lifetime_years} Jahre",
    ]
    right = [
        f"CAPEX gesamt: {capex_total:,.0f} €",
        f"OPEX p.a.: {opex_annual:,.0f} €",
        f"FK-Anteil: {loan_share} % | Zins: {interest_rate} % | Tilgung: {repayment_years} J",
        f"Preis EV: {price_self_consumption:.3f} €/kWh | EEG: {price_feed_in:.3f} €/kWh",
        f"Preissteigerung: {inflation_rate*100:.1f} %",
    ]
    for row in range(max(len(left), len(right))):
        if row < len(left):
            c.drawString(margin, y, left[row])
        if row < len(right):
            c.drawString(margin + 260, y, right[row])
        y -= 12

    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor(PRIMARY_DARK))
    c.drawString(margin, y, "KPI:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    y -= 12
    c.drawString(margin, y, f"Amortisationsjahr: {amort_year}")
    y -= 12
    irr_text = "n/a" if irr_estimate is None else f"{irr_estimate:.2%}"
    c.drawString(margin, y, f"IRR: {irr_text}")
    y -= 12
    c.drawString(margin, y, f"LCOE: {lcoe:.4f} €/kWh")
    y -= 18

    # Diagramme platzieren (ggf. auf mehrere Seiten)
    for img_buf, title in [(buf_fig, "Cashflow & Break-even"),
                           (buf_fig1, "Effektiver Mieterstrompreis"),
                           (buf_fig2, "Jährlicher Gewinn")]:
        if y < 250:
            c.showPage()
            y = height - margin
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor(PRIMARY_DARK))
        c.drawString(margin, y, title)
        y -= 6
        c.setFillColor(colors.black)
        y -= 200
        c.drawImage(ImageReader(img_buf), margin, y, width=width-2*margin, height=190, preserveAspectRatio=True, mask='auto')
        y -= 24

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawString(margin, 20, "Automatisch erstellt mit Qrauts PV-Dashboard – simply different")
    c.save()
    pdf_bytes.seek(0)
    return pdf_bytes

# ------------- Downloads UI ---------------
st.header("📥 Export")

excel_bytes = build_excel_bytes()
st.download_button(
    label="💾 Excel-Arbeitsmappe herunterladen",
    data=excel_bytes,
    file_name="PV_Kalkulation_Qrauts.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

if REPORTLAB_AVAILABLE:
    pdf_bytes = build_pdf_bytes()
    st.download_button(
        label="📄 PDF-Ergebnisbericht herunterladen",
        data=pdf_bytes,
        file_name="PV_Ergebnisbericht_Qrauts.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.info("Für den PDF-Export bitte `reportlab` in den Abhängigkeiten installieren (requirements.txt).")
