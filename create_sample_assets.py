import os
from PIL import Image, ImageDraw, ImageFont

uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(uploads_dir, exist_ok=True)

def create_receipt_image(filename, title, details, bg_color="#F8FAFC", accent_color="#173B68"):
    width, height = 480, 560
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Outer border
    draw.rectangle([8, 8, width-8, height-8], outline="#CBD5E1", width=2)
    # Inner decorative receipt border
    draw.rectangle([18, 18, width-18, height-18], outline="#E2E8F0", width=1)
    
    # Header bar
    draw.rectangle([18, 18, width-18, 90], fill=accent_color)
    
    # Text helper
    try:
        font_large = ImageFont.truetype("arial.ttf", 20)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_body = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 15)
        font_price = ImageFont.truetype("arialbd.ttf", 26)
    except IOError:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_price = ImageFont.load_default()

    draw.text((width//2, 42), "MALOLOS CITY TERMINAL HUB", fill="#FFFFFF", font=font_large, anchor="mm")
    draw.text((width//2, 68), "COMMUTER FARE DISPATCH SLIP / EVIDENCE", fill="#93C5FD", font=font_sub, anchor="mm")
    
    # Title
    draw.text((36, 120), title, fill="#0F172A", font=font_bold)
    draw.line([36, 145, width-36, 145], fill="#E2E8F0", width=1)
    
    y = 165
    for label, val in details:
        draw.text((36, y), label, fill="#64748B", font=font_body)
        draw.text((width-36, y), val, fill="#0F172A", font=font_bold, anchor="ra")
        y += 36
        draw.line([36, y-10, width-36, y-10], fill="#F1F5F9", width=1)
    
    # Total Box
    draw.rectangle([36, y+10, width-36, y+75], fill="#EFF6FF", outline="#BFDBFE", width=1)
    draw.text((50, y+42), "TOTAL COLLECTED", fill="#1E40AF", font=font_bold, anchor="lm")
    draw.text((width-50, y+42), details[0][1] if details else "₱0.00", fill="#1E3A8A", font=font_price, anchor="rm")
    
    # Footer notice
    draw.text((width//2, height-40), "Research Evidence Copy - Malolos FareWatch", fill="#94A3B8", font=font_sub, anchor="mm")
    
    path = os.path.join(uploads_dir, filename)
    img.save(path, "PNG")
    print(f"Generated {path}")

create_receipt_image(
    "evidence_sample_1.png",
    "Tricycle Commuter Receipt #00412",
    [
        ("Fare Collected", "₱25.00"),
        ("Official Standard Fare", "₱20.00"),
        ("Origin - Destination", "Xentro Mall -> Malolos Proper"),
        ("Tricycle Body No.", "TM-0418"),
        ("Date & Time", "Oct 3, 2026 08:24 AM"),
        ("Payment Type", "Cash On Board"),
    ],
    bg_color="#FFFFFF",
    accent_color="#173B68"
)

create_receipt_image(
    "evidence_sample_2.png",
    "Terminal Dispatch Stub #00389",
    [
        ("Fare Collected", "₱15.00"),
        ("Official Standard Fare", "₱15.00"),
        ("Origin - Destination", "Xentro Mall -> Calumpit"),
        ("Tricycle Body No.", "TC-1102"),
        ("Date & Time", "Oct 3, 2026 07:12 AM"),
        ("Payment Type", "Terminal Booth"),
    ],
    bg_color="#FFFFFF",
    accent_color="#0D9488"
)

create_receipt_image(
    "evidence_sample_3.png",
    "Fare Receipt / Body Sign #00507",
    [
        ("Fare Collected", "₱30.00"),
        ("Official Standard Fare", "₱20.00"),
        ("Origin - Destination", "Xentro Mall -> Bulihan"),
        ("Tricycle Body No.", "TB-0749"),
        ("Date & Time", "Oct 3, 2026 09:45 AM"),
        ("Payment Type", "Cash On Board"),
    ],
    bg_color="#FFFFFF",
    accent_color="#C026D3"
)

create_receipt_image(
    "evidence_sample_4.png",
    "Passenger Dispatch Ticket #00224",
    [
        ("Fare Collected", "₱25.00"),
        ("Official Standard Fare", "₱25.00"),
        ("Origin - Destination", "Xentro Mall -> Calumpit"),
        ("Tricycle Body No.", "TC-0883"),
        ("Date & Time", "Oct 2, 2026 04:30 PM"),
        ("Payment Type", "Terminal Cash"),
    ],
    bg_color="#FFFFFF",
    accent_color="#2563EB"
)
