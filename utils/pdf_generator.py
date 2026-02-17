"""
PDF Report Generator for Financial Statements

Generates professional PDF reports with charts and metrics.
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
import tempfile
import os


def create_monthly_pdf_report(
    period_label: str,
    metrics: dict,
    health: dict,
    periods_df: pd.DataFrame = None,
    gst_stats: dict = None
) -> BytesIO:
    """
    Generate a comprehensive PDF report for monthly financial statement.
    
    Args:
        period_label: Month label (e.g., "2026-01")
        metrics: Financial metrics dictionary
        health: Financial health assessment
        periods_df: DataFrame with historical period data for charts
        gst_stats: GST statistics dictionary
    
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # Title
    elements.append(Paragraph(f"Financial Statement Report", title_style))
    elements.append(Paragraph(f"Period: {period_label}", ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#7F8C8D'),
        alignment=TA_CENTER,
        spaceAfter=20
    )))
    
    # Generation date
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                            ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=9, 
                                         textColor=colors.grey, alignment=TA_RIGHT, spaceAfter=20)))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Financial Health Section
    elements.append(Paragraph("Financial Health Overview", heading_style))
    
    health_status_colors = {
        "healthy": colors.HexColor('#27AE60'),
        "moderate": colors.HexColor('#F39C12'),
        "critical": colors.HexColor('#E74C3C')
    }
    
    health_color = health_status_colors.get(health.get('status', 'moderate'), colors.grey)
    
    health_data = [
        ['Status', 'Score'],
        [health.get('status', 'N/A').upper(), f"{health.get('score', 0)}/100"]
    ]
    
    health_table = Table(health_data, colWidths=[3*inch, 2*inch])
    health_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (0, 1), health_color),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(health_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Key Financial Metrics
    elements.append(Paragraph("Key Financial Metrics", heading_style))
    
    metrics_data = [
        ['Metric', 'Amount (₹)', 'Details'],
        ['Revenue', f"₹{metrics.get('revenue', 0):,.2f}", ''],
        ['Expenses', f"₹{metrics.get('expenses', 0):,.2f}", ''],
        ['Profit', f"₹{metrics.get('profit', 0):,.2f}", f"{metrics.get('profit_margin', 0):.2f}% margin"],
        ['Outstanding Receivables', f"₹{metrics.get('receivables', 0):,.2f}", f"{metrics.get('receivables_ratio', 0):.2f}% of revenue"],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # GST Section (if available)
    if gst_stats:
        elements.append(Paragraph("GST Analysis", heading_style))
        
        gst_data = [
            ['Category', 'Amount (₹)'],
            ['ITC Eligible', f"₹{gst_stats.get('itc_eligible', 0):,.2f}"],
            ['Blocked Credit', f"₹{gst_stats.get('blocked_credit', 0):,.2f}"],
            ['Non-Applicable', f"₹{gst_stats.get('non_applicable', 0):,.2f}"],
            ['Review Required', f"₹{gst_stats.get('review_required', 0):,.2f}"],
            ['ITC Health Score', f"{gst_stats.get('itc_health_score', 0):.2f}%"],
        ]
        
        gst_table = Table(gst_data, colWidths=[3*inch, 2*inch])
        gst_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(gst_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Risk Alerts
    if health.get('risks'):
        elements.append(Paragraph("Risk Alerts & Recommendations", heading_style))
        
        for i, risk in enumerate(health.get('risks', []), 1):
            risk_type = risk.get('type', 'warning').upper()
            risk_color = colors.HexColor('#E74C3C') if risk_type == 'CRITICAL' else colors.HexColor('#F39C12')
            
            elements.append(Paragraph(
                f"<b>[{risk_type}]</b> {risk.get('message', 'N/A')}", 
                ParagraphStyle('RiskStyle', parent=styles['Normal'], fontSize=10, 
                             textColor=risk_color, spaceAfter=6)
            ))
            elements.append(Paragraph(
                f"💡 <i>{risk.get('recommendation', 'N/A')}</i>", 
                ParagraphStyle('RecommendationStyle', parent=styles['Normal'], fontSize=9, 
                             leftIndent=20, spaceAfter=12, textColor=colors.HexColor('#34495E'))
            ))
    else:
        elements.append(Paragraph("✅ No risks detected. Financial health is stable.", normal_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Add charts if historical data is provided
    if periods_df is not None and not periods_df.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("Historical Trends", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create and add charts
        chart_images = _generate_chart_images(periods_df)
        
        for img_path in chart_images:
            if os.path.exists(img_path):
                img = Image(img_path, width=6.5*inch, height=3*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        "<i>This report was automatically generated by Dinero AI - Financial Analysis System</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                      textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(elements)
    
    # Clean up temporary image files
    if periods_df is not None and not periods_df.empty:
        for img_path in chart_images:
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except:
                    pass
    
    buffer.seek(0)
    return buffer


def _generate_chart_images(periods_df: pd.DataFrame) -> list:
    """
    Generate chart images from periods data.
    
    Args:
        periods_df: DataFrame with period metrics
        
    Returns:
        List of temporary file paths for chart images
    """
    chart_files = []
    
    try:
        # Revenue vs Expenses Chart
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=periods_df['period'], y=periods_df['revenue'], 
                                  mode='lines+markers', name='Revenue', 
                                  line=dict(color='#27AE60', width=3)))
        fig1.add_trace(go.Scatter(x=periods_df['period'], y=periods_df['expenses'], 
                                  mode='lines+markers', name='Expenses', 
                                  line=dict(color='#E74C3C', width=3)))
        fig1.update_layout(title='Revenue vs Expenses Trend', 
                          xaxis_title='Period', yaxis_title='Amount (₹)',
                          height=400, showlegend=True)
        
        temp1 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig1.write_image(temp1.name, width=800, height=400)
        chart_files.append(temp1.name)
        
        # Profit Trend Chart
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=periods_df['period'], y=periods_df['profit'], 
                             name='Profit',
                             marker=dict(color=periods_df['profit'], 
                                       colorscale='RdYlGn',
                                       showscale=True)))
        fig2.update_layout(title='Profit Trend', 
                          xaxis_title='Period', yaxis_title='Profit (₹)',
                          height=400)
        
        temp2 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig2.write_image(temp2.name, width=800, height=400)
        chart_files.append(temp2.name)
        
        # Profit Margin Chart
        if 'profit_margin' in periods_df.columns:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=periods_df['period'], y=periods_df['profit_margin'], 
                                     mode='lines+markers', name='Profit Margin %',
                                     line=dict(color='#3498DB', width=3)))
            fig3.add_hline(y=10, line_dash="dash", line_color="green", 
                          annotation_text="Target: 10%")
            fig3.update_layout(title='Profit Margin Trend (%)', 
                              xaxis_title='Period', yaxis_title='Margin (%)',
                              height=400)
            
            temp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            fig3.write_image(temp3.name, width=800, height=400)
            chart_files.append(temp3.name)
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        # Return empty list if chart generation fails
        return []
    
    return chart_files
