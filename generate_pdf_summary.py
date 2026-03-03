#!/usr/bin/env python3
"""
Generate PDF Summary Document
=============================

Converts the PROJECT_SUMMARY.md to a nicely formatted PDF document.
Uses only Python standard library - no external dependencies required.
"""

import os
import re
from datetime import datetime


def markdown_to_html(md_content):
    """Convert Markdown to HTML"""
    html = md_content
    
    # Escape HTML special characters (except for our conversions)
    # html = html.replace('&', '&amp;')  # Skip to preserve emojis
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)```', lambda m: f'<pre class="code-block"><code>{m.group(2)}</code></pre>', html, flags=re.DOTALL)
    
    # Horizontal rules
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
    
    # Tables
    lines = html.split('\n')
    in_table = False
    new_lines = []
    
    for i, line in enumerate(lines):
        if '|' in line and not line.strip().startswith('```'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            
            if cells and all(re.match(r'^[-:]+$', c) for c in cells):
                # This is a separator row, skip it
                continue
            elif cells:
                if not in_table:
                    new_lines.append('<table>')
                    in_table = True
                    # First row is header
                    new_lines.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
                else:
                    new_lines.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
            else:
                if in_table:
                    new_lines.append('</table>')
                    in_table = False
                new_lines.append(line)
        else:
            if in_table:
                new_lines.append('</table>')
                in_table = False
            new_lines.append(line)
    
    if in_table:
        new_lines.append('</table>')
    
    html = '\n'.join(new_lines)
    
    # Checkboxes
    html = re.sub(r'- \[ \]', r'<span class="checkbox">☐</span>', html)
    html = re.sub(r'- \[x\]', r'<span class="checkbox">☑</span>', html)
    
    # Unordered lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', html)
    
    # Ordered lists
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # Paragraphs (lines that aren't already wrapped)
    lines = html.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not any(stripped.startswith(tag) for tag in ['<h', '<p', '<ul', '<ol', '<li', '<table', '<tr', '<pre', '<hr', '</']) and not stripped.endswith('>'):
            result.append(f'<p>{line}</p>')
        else:
            result.append(line)
    
    html = '\n'.join(result)
    
    return html


def create_html_document(md_content):
    """Create a complete HTML document with styling"""
    
    html_body = markdown_to_html(md_content)
    
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salesforce Flow AI Implementation - Project Summary</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-size: 11pt;
        }}
        
        h1 {{
            color: #0176d3;
            border-bottom: 3px solid #0176d3;
            padding-bottom: 10px;
            font-size: 24pt;
            margin-top: 30px;
        }}
        
        h2 {{
            color: #032d60;
            border-bottom: 2px solid #e5e5e5;
            padding-bottom: 8px;
            font-size: 16pt;
            margin-top: 25px;
        }}
        
        h3 {{
            color: #444;
            font-size: 13pt;
            margin-top: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        
        th {{
            background-color: #0176d3;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        tr:hover {{
            background-color: #f1f1f1;
        }}
        
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
            font-size: 9pt;
            color: #d63384;
        }}
        
        pre {{
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 9pt;
            line-height: 1.4;
        }}
        
        pre code {{
            background-color: transparent;
            color: #d4d4d4;
            padding: 0;
        }}
        
        .code-block {{
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        
        ul, ol {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        
        li {{
            margin: 5px 0;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #e5e5e5;
            margin: 30px 0;
        }}
        
        .checkbox {{
            font-size: 14pt;
            margin-right: 5px;
        }}
        
        strong {{
            color: #032d60;
        }}
        
        /* Print-specific styles */
        @media print {{
            body {{
                font-size: 10pt;
            }}
            
            h1 {{
                page-break-before: always;
            }}
            
            h1:first-of-type {{
                page-break-before: avoid;
            }}
            
            pre, table {{
                page-break-inside: avoid;
            }}
        }}
        
        /* Header styling */
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #0176d3 0%, #032d60 100%);
            color: white;
            border-radius: 10px;
        }}
        
        .header h1 {{
            color: white;
            border: none;
            margin: 0;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        
        /* Footer */
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e5e5e5;
            text-align: center;
            color: #666;
            font-size: 9pt;
        }}
        
        /* Architecture diagram box */
        pre:has(code:contains("┌")) {{
            font-family: 'SF Mono', Monaco, monospace;
            background-color: #f8f9fa;
            color: #333;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Salesforce Flow AI Implementation</h1>
        <p>Project Summary Document</p>
        <p>Generated: {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    {html_body}
    
    <div class="footer">
        <p><strong>Salesforce Flow AI Implementation</strong></p>
        <p>© 2026 Saurabh Yadav | Generated with Python</p>
        <p>This document provides a comprehensive overview of the AI-powered Salesforce Flow analysis system.</p>
    </div>
</body>
</html>
'''
    return html_doc


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    GENERATE PDF SUMMARY DOCUMENT                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Read the markdown file
    md_file = os.path.join(os.path.dirname(__file__), 'PROJECT_SUMMARY.md')
    
    if not os.path.exists(md_file):
        print(f"❌ PROJECT_SUMMARY.md not found!")
        return
    
    print(f"📖 Reading: PROJECT_SUMMARY.md")
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    print(f"✅ Read {len(md_content)} characters")
    
    # Convert to HTML
    print(f"🔄 Converting Markdown to HTML...")
    html_content = create_html_document(md_content)
    
    # Save HTML file
    html_file = os.path.join(os.path.dirname(__file__), 'PROJECT_SUMMARY.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created: PROJECT_SUMMARY.html")
    
    # Try to create PDF using different methods
    pdf_file = os.path.join(os.path.dirname(__file__), 'PROJECT_SUMMARY.pdf')
    pdf_created = False
    
    # Method 1: Try using cupsfilter (macOS)
    print(f"\n📄 Generating PDF...")
    
    try:
        import subprocess
        
        # Method: Use macOS textutil + cupsfilter
        result = subprocess.run(
            ['cupsfilter', html_file],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0:
            with open(pdf_file, 'wb') as f:
                f.write(result.stdout)
            pdf_created = True
            print(f"✅ Created PDF using cupsfilter")
    except Exception as e:
        pass
    
    # Method 2: Try wkhtmltopdf if available
    if not pdf_created:
        try:
            import subprocess
            result = subprocess.run(
                ['which', 'wkhtmltopdf'],
                capture_output=True
            )
            if result.returncode == 0:
                subprocess.run(
                    ['wkhtmltopdf', '--quiet', html_file, pdf_file],
                    timeout=60
                )
                if os.path.exists(pdf_file):
                    pdf_created = True
                    print(f"✅ Created PDF using wkhtmltopdf")
        except:
            pass
    
    # Method 3: Try weasyprint if available
    if not pdf_created:
        try:
            from weasyprint import HTML
            HTML(filename=html_file).write_pdf(pdf_file)
            pdf_created = True
            print(f"✅ Created PDF using weasyprint")
        except ImportError:
            pass
        except Exception as e:
            pass
    
    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    print(f"""
✅ Files Generated:

   📄 HTML Version (viewable in any browser):
      {html_file}
""")
    
    if pdf_created:
        file_size = os.path.getsize(pdf_file) / 1024
        print(f"""   📕 PDF Version:
      {pdf_file}
      Size: {file_size:.1f} KB
""")
    else:
        print(f"""   ⚠️  PDF Generation requires additional tools.
   
   To create PDF, you can:
   
   Option 1: Open HTML in browser and Print to PDF
      • Open: {html_file}
      • Press Cmd+P → Save as PDF
   
   Option 2: Install wkhtmltopdf
      brew install wkhtmltopdf
      wkhtmltopdf PROJECT_SUMMARY.html PROJECT_SUMMARY.pdf
   
   Option 3: Install weasyprint
      pip install weasyprint
      python -c "from weasyprint import HTML; HTML('PROJECT_SUMMARY.html').write_pdf('PROJECT_SUMMARY.pdf')"
""")
    
    print(f"""
🚀 Quick View Commands:

   # Open HTML in default browser
   open PROJECT_SUMMARY.html
   
   # Open in VS Code
   code PROJECT_SUMMARY.html
""")


if __name__ == "__main__":
    main()
