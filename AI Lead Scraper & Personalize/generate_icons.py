# Icon Generation Script
# Generates PNG icons with gradient background for Chrome Extension

from PIL import Image, ImageDraw, ImageFont
import os

def create_gradient_icon(size):
    """Create icon with gradient background and AI text"""
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create purple gradient background
    for y in range(size):
        # Gradient from #667eea to #764ba2
        ratio = y / size
        r = int(102 + (118 - 102) * ratio)
        g = int(126 + (75 - 126) * ratio)
        b = int(234 + (162 - 234) * ratio)
        draw.rectangle([(0, y), (size, y + 1)], fill=(r, g, b))
    
    # Add rounded corners
    corner_radius = max(3, size // 8)
    
    # Create mask for rounded corners
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size, size)], corner_radius, fill=255)
    
    # Apply mask
    img.putalpha(mask)
    
    # Add text
    text = "AI"
    font_size = size // 2
    
    try:
        # Try different font paths for Windows
        for font_path in ["arial.ttf", "C:\\Windows\\Fonts\\arial.ttf", "segoeui.ttf", "C:\\Windows\\Fonts\\segoeui.ttf"]:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Get text dimensions and center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # Draw white text
    draw.text((x, y), text, fill='white', font=font)
    
    return img

# Generate icons
if __name__ == "__main__":
    icon_dir = os.path.join(os.path.dirname(__file__), 'icons')
    os.makedirs(icon_dir, exist_ok=True)
    
    print("🎨 Generating extension icons...")
    
    for size in [16, 48, 128]:
        icon = create_gradient_icon(size)
        icon_path = os.path.join(icon_dir, f'icon{size}.png')
        icon.save(icon_path, 'PNG')
        print(f"✅ Created icon{size}.png")
    
    print("\n🎉 All icons generated successfully!")
    print(f"📁 Icons saved to: {icon_dir}")
