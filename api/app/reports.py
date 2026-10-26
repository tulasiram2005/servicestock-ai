from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .services import artifact


def review_pack(store):
    analytics = artifact(store, "analytics")
    benchmark = artifact(store, "benchmark")
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(8.5 * inch, 11 * inch), rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    story = [Paragraph("ServiceStock AI | Review pack", styles["Title"]),
             Paragraph("SYNTHETIC COST ASSUMPTIONS - FREE-TIER DEMO", styles["Heading2"]),
             Paragraph("Public car-parts demand. Costs, lead times, criticality, comments and supplier records are synthetic. No SAP system was used.", styles["BodyText"]),
             Spacer(1, 16)]
    def section(title, text):
        story.append(Paragraph(escape(title), styles["Heading2"]))
        story.append(Paragraph(escape(text), styles["BodyText"]))
        story.append(Spacer(1, 12))
    section("Executive summary", "All figures below are simulated decision-support outputs, not realized business savings. Negative working capital freed means additional capital is required.")
    table_rows = [["Metric", "Measured simulation result"]]
    for key, value in analytics["kpis"].items():
        table_rows.append([key.replace("_", " "), f"{value:,.4f}"])
    table = Table(table_rows, colWidths=[280, 220])
    table.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0),colors.HexColor("#173f35")),
                              ("TEXTCOLOR",(0,0),(-1,0),colors.white),("BOTTOMPADDING",(0,0),(-1,-1),10),
                              ("GRID",(0,0),(-1,-1),0.4,colors.lightgrey)]))
    story.append(table)
    section("Methodology", "Rolling-origin forecast evaluation with separate validation and held-out periods. Empirical demand resampling and lognormal lead times, 10,000 seeded draws per part. Grid scenarios are precomputed. The policy minimizes modeled cost among feasible candidates at an equal or better fill rate.")
    section("Demand provenance", str(benchmark["dataset"]["note"]))
    section("Finance", f'Working capital USD {analytics["finance"]["working_capital"]:,.2f}; annual carrying cost USD {analytics["finance"]["carrying_cost"]:,.2f}. Inventory days: {analytics["finance"]["inventory_days"]}.')
    section("Top annual cost opportunities", "Ranked by estimated annual cost savings, which can be negative.")
    recommendations = sorted(analytics["policies"], key=lambda item:item["annual_savings"], reverse=True)[:10]
    table = Table([["Part", "Stock", "Annual savings USD", "Capital freed USD"]] +
                  [[item["part_id"], str(item["optimized"]["stock"]), f'{item["annual_savings"]:,.2f}',
                    f'{item["working_capital_freed"]:,.2f}'] for item in recommendations], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
    story.append(table)
    section("Limitations", "Only the first 24 source series are included. The upstream dataset replaces missing values with zeros. Inventory simulation represents independent lead-time cycles, not a validated replenishment system. NLP labels and regression outcomes are synthetic; zero-shot comparison is not measured. Production capacity and deployed latency are not measured.")
    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.drawString(48, 25, "Synthetic cost assumptions | ServiceStock AI")
        canvas.drawRightString(560, 25, str(document.page))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
