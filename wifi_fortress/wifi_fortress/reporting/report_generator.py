from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import json
import matplotlib.pyplot as plt
import io

class HorizontalLine(Flowable):
    """Custom flowable for drawing horizontal lines"""
    def __init__(self, width, thickness=1, color=colors.black):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

class ReportGenerator:
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a237e')
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12
        )
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3949ab'),
            spaceAfter=10
        )
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14
        )
        self.alert_style = ParagraphStyle(
            'CustomAlert',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.red,
            leading=14
        )
        
    def create_network_security_report(self, scan_results: List[Dict[str, Any]], 
                                     threat_data: Optional[Dict] = None,
                                     performance_data: Optional[Dict] = None) -> str:
        """Create a comprehensive PDF security report"""
        
        # Add threat data if not provided
        if threat_data is None:
            threat_data = {
                'attacks_blocked': 0,
                'suspicious_ips': [],
                'vulnerabilities': [],
                'threat_types': {'malware': 0, 'intrusion': 0, 'dos': 0}
            }
            
        # Add performance data if not provided
        if performance_data is None:
            performance_data = {
                'signal_strength': [],
                'bandwidth_usage': [],
                'error_rates': [],
                'timestamps': []
            }
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'security_report_{timestamp}.pdf')
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build the document content
        story = []
        
        # Title and Logo
        title = Paragraph("WiFi Fortress Security Report", self.title_style)
        story.append(title)
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        summary_data = [
            [Paragraph("Total Networks Scanned:", self.normal_style),
             Paragraph(str(len(scan_results)), self.normal_style)],
            [Paragraph("Threats Detected:", self.normal_style),
             Paragraph(str(len(threat_data['suspicious_ips'])), self.normal_style)],
            [Paragraph("Attacks Blocked:", self.normal_style),
             Paragraph(str(threat_data['attacks_blocked']), self.normal_style)],
            [Paragraph("Overall Security Score:", self.normal_style),
             Paragraph(self.calculate_security_score(scan_results, threat_data), self.normal_style)]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f3f3')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#000000')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbdefb'))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Threat Analysis
        story.append(Paragraph("Threat Analysis", self.heading_style))
        story.append(self.create_threat_analysis(threat_data))
        story.append(PageBreak())
        
        # Network Details
        story.append(Paragraph("Network Analysis", self.heading_style))
        story.append(self.create_network_analysis(scan_results))
        story.append(PageBreak())
        
        # Performance Metrics
        story.append(Paragraph("Performance Metrics", self.heading_style))
        story.append(self.create_performance_charts(performance_data))
        story.append(PageBreak())
        
        # Security Recommendations
        story.append(Paragraph("Security Recommendations", self.heading_style))
        story.append(self.create_security_recommendations(scan_results, threat_data))
        
        # Build the PDF
        doc.build(story)
        return filename
    
    def calculate_security_score(self, scan_results: List[Dict], threat_data: Dict) -> str:
        """Calculate overall security score based on various metrics"""
        score = 100
        
        # Deduct points for each vulnerability
        score -= len(threat_data['vulnerabilities']) * 10
        
        # Deduct points for suspicious IPs
        score -= len(threat_data['suspicious_ips']) * 5
        
        # Deduct points for weak security protocols in networks
        for network in scan_results:
            security = network.get('security', '').lower()
            if 'wep' in security:
                score -= 20
            elif 'wpa' in security and 'wpa3' not in security:
                score -= 5
            elif 'open' in security:
                score -= 15
        
        # Ensure score stays within 0-100
        score = max(0, min(100, score))
        
        # Return score with grade
        if score >= 90:
            return f"A ({score}%)"
        elif score >= 80:
            return f"B ({score}%)"
        elif score >= 70:
            return f"C ({score}%)"
        elif score >= 60:
            return f"D ({score}%)"
        else:
            return f"F ({score}%)"
    
    def create_threat_analysis(self, threat_data: Dict) -> Table:
        """Create a detailed threat analysis section"""
        # Create pie chart for threat types
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        pie.data = list(threat_data['threat_types'].values())
        pie.labels = list(threat_data['threat_types'].keys())
        pie.slices.strokeWidth = 0.5
        drawing.add(pie)
        
        # Create threat summary
        threat_summary = [
            [Paragraph("Threat Category", self.subheading_style),
             Paragraph("Count", self.subheading_style),
             Paragraph("Severity", self.subheading_style)]
        ]
        
        for category, count in threat_data['threat_types'].items():
            severity = "High" if count > 5 else "Medium" if count > 2 else "Low"
            style = self.alert_style if severity == "High" else self.normal_style
            
            threat_summary.append([
                Paragraph(category.title(), self.normal_style),
                Paragraph(str(count), self.normal_style),
                Paragraph(severity, style)
            ])
        
        # Create and style the table
        table = Table(threat_summary, colWidths=[2*inch, inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def create_network_analysis(self, scan_results: List[Dict]) -> Table:
        """Create a detailed network analysis section"""
        # Analyze security protocols
        security_counts = {}
        channel_usage = {}
        signal_strengths = []
        
        for network in scan_results:
            # Count security protocols
            security = network.get('security', 'Unknown')
            security_counts[security] = security_counts.get(security, 0) + 1
            
            # Count channel usage
            channel = network.get('channel', 0)
            channel_usage[channel] = channel_usage.get(channel, 0) + 1
            
            # Collect signal strengths
            if 'signal_strength' in network:
                signal_strengths.append(network['signal_strength'])
        
        # Create analysis table
        analysis_data = [
            [Paragraph("Analysis Category", self.subheading_style),
             Paragraph("Details", self.subheading_style)]
        ]
        
        # Add security protocol analysis
        security_text = ", ".join([f"{proto}: {count}" 
                                for proto, count in security_counts.items()])
        analysis_data.append([
            Paragraph("Security Protocols", self.normal_style),
            Paragraph(security_text, self.normal_style)
        ])
        
        # Add channel analysis
        busy_channels = [ch for ch, count in channel_usage.items() 
                       if count > 2 and ch != 0]
        channel_text = f"Busy channels: {', '.join(map(str, busy_channels))}" \
                      if busy_channels else "No channel congestion detected"
        analysis_data.append([
            Paragraph("Channel Analysis", self.normal_style),
            Paragraph(channel_text, self.normal_style)
        ])
        
        # Add signal strength analysis
        if signal_strengths:
            avg_signal = sum(signal_strengths) / len(signal_strengths)
            signal_text = f"Average: {avg_signal:.1f}%, "
            signal_text += "Good" if avg_signal > 70 else \
                          "Fair" if avg_signal > 50 else "Poor"
        else:
            signal_text = "No signal strength data available"
            
        analysis_data.append([
            Paragraph("Signal Strength", self.normal_style),
            Paragraph(signal_text, self.normal_style)
        ])
        
        # Create and style the table
        table = Table(analysis_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        return table
    
    def create_performance_charts(self, performance_data: Dict) -> Drawing:
        """Create performance metric charts"""
        drawing = Drawing(500, 200)
        
        # Create line chart
        chart = HorizontalLineChart()
        chart.x = 50
        chart.y = 50
        chart.height = 125
        chart.width = 400
        
        # Add data
        chart.data = [
            performance_data['signal_strength'],
            performance_data['bandwidth_usage'],
            performance_data['error_rates']
        ]
        
        # Customize chart
        chart.lines[0].strokeColor = colors.blue
        chart.lines[1].strokeColor = colors.green
        chart.lines[2].strokeColor = colors.red
        
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 100
        chart.valueAxis.valueStep = 20
        
        # Add legend
        chart.categoryAxis.categoryNames = performance_data['timestamps']
        chart.categoryAxis.labels.boxAnchor = 'ne'
        chart.categoryAxis.labels.dx = 8
        chart.categoryAxis.labels.dy = -2
        chart.categoryAxis.labels.angle = 30
        
        drawing.add(chart)
        return drawing
    
    def create_security_recommendations(self, scan_results: List[Dict], 
                                      threat_data: Dict) -> Table:
        """Create detailed security recommendations based on analysis"""
        recommendations = [
            [Paragraph("Category", self.subheading_style),
             Paragraph("Recommendation", self.subheading_style),
             Paragraph("Priority", self.subheading_style)]
        ]
        
        # Network Security
        has_weak_security = any('wep' in net.get('security', '').lower() 
                              for net in scan_results)
        if has_weak_security:
            recommendations.append([
                Paragraph("Network Security", self.normal_style),
                Paragraph("Upgrade networks using WEP to WPA3", self.normal_style),
                Paragraph("High", self.alert_style)
            ])
        
        # Threat Response
        if threat_data['suspicious_ips']:
            recommendations.append([
                Paragraph("Threat Response", self.normal_style),
                Paragraph(f"Block {len(threat_data['suspicious_ips'])} suspicious IPs", 
                         self.normal_style),
                Paragraph("High", self.alert_style)
            ])
        
        # Channel Optimization
        channel_conflicts = self._analyze_channel_conflicts(scan_results)
        if channel_conflicts:
            recommendations.append([
                Paragraph("Channel Optimization", self.normal_style),
                Paragraph("Redistribute networks across channels to reduce interference",
                         self.normal_style),
                Paragraph("Medium", self.normal_style)
            ])
        
        # Create and style the table
        table = Table(recommendations, colWidths=[1.5*inch, 4*inch, inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        return table
    
    def _analyze_channel_conflicts(self, scan_results: List[Dict]) -> bool:
        """Analyze network channels for conflicts"""
        channel_count = {}
        for network in scan_results:
            channel = network.get('channel', 0)
            if channel:
                channel_count[channel] = channel_count.get(channel, 0) + 1
        
        # Check if any channel has more than 3 networks
        return any(count > 3 for count in channel_count.values())
        
    def create_incident_report(self, incident_data: Dict[str, Any]) -> str:
        """Create a PDF report for security incidents"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'incident_report_{timestamp}.pdf')
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        title = Paragraph("Security Incident Report", self.title_style)
        story.append(title)
        
        # Incident Details
        details = [
            Paragraph("Incident Details", self.heading_style),
            Paragraph(f"Date: {incident_data.get('date', 'Unknown')}", self.normal_style),
            Paragraph(f"Type: {incident_data.get('type', 'Unknown')}", self.normal_style),
            Paragraph(f"Severity: {incident_data.get('severity', 'Unknown')}", self.normal_style),
            Spacer(1, 12),
            Paragraph("Description", self.heading_style),
            Paragraph(incident_data.get('description', 'No description provided'), self.normal_style),
            Spacer(1, 12)
        ]
        story.extend(details)
        
        # Actions Taken
        if 'actions' in incident_data:
            story.append(Paragraph("Actions Taken", self.heading_style))
            for action in incident_data['actions']:
                story.append(Paragraph(f"• {action}", self.normal_style))
        
        # Recommendations
        if 'recommendations' in incident_data:
            story.extend([
                Spacer(1, 12),
                Paragraph("Recommendations", self.heading_style)
            ])
            for rec in incident_data['recommendations']:
                story.append(Paragraph(f"• {rec}", self.normal_style))
        
        # Build the PDF
        doc.build(story)
        return filename
