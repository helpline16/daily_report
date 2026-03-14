import re

with open(r'c:\Users\admin\Desktop\cyber multiple accoun with DA and ACK\src\ui_styling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the entire COLORS dictionary
old_colors_regex = r"COLORS\s*=\s*\{.*?\}(?=\n\s*\n|$$PAGE_INFO$$|PAGE_INFO)"
new_colors = """COLORS = {
    # Primary - Midnight Slate & Neon
    'deep_ocean': '#060608',       # Dark midnight background
    'ocean_blue': '#0D0E15',       # Darker slate
    'water_blue': '#8B5CF6',       # Vibrant Neon Purple
    'sky_blue': '#00F5FF',         # Electric Cyan
    'light_aqua': '#D946EF',       # Neon Magenta
    'foam_white': '#FFFFFF',       # Bright white
    
    # Accent - Holographic
    'coral': '#EC4899',            # Pink
    'teal': '#10B981',             # Emerald green
    'mint': '#6EE7B7',             # Light Mint
    'seafoam': '#A78BFA',          # Soft bright indigo
    
    # Background
    'background': '#020203',       # Absolute black
    'background_card': 'rgba(15, 15, 20, 0.65)', # Sleek dark card
    'text_primary': '#F3F4F6',     # Off White
    'text_secondary': '#00F5FF',   # Cyan text
    'text_muted': '#9CA3AF',       # Gray text
    
    # Status colors
    'success': '#10B981',          # Emerald
    'warning': '#F59E0B',          # Amber
    'error': '#EF4444',            # Red
    'info': '#3B82F6',             # Blue
    
    # Glass effect
    'glass_bg': 'rgba(255, 255, 255, 0.03)',
    'glass_border': 'rgba(255, 255, 255, 0.08)',
    
    # Additional
    'border': '#1F2937',
    'hover': 'rgba(139, 92, 246, 0.15)',
    'shadow': 'rgba(0, 245, 255, 0.2)'
}"""
content = re.sub(old_colors_regex, new_colors, content, flags=re.DOTALL)

# Replace hardcoded marine blue rgba values with premium midnight slate grey/purple rgba
# 1, 11, 20 -> 10, 10, 14 (darkest grey)
# 4, 42, 79 -> 22, 22, 26 (slate grey)
# 10, 116, 218 -> 139, 92, 246 (neon purple)
# 13, 226, 255 -> 0, 245, 255 (neon cyan)
# 0, 5, 10 -> 4, 4, 6 (absolute void, sidebar bg base)

content = content.replace("1, 11, 20", "10, 10, 14")
content = content.replace("4, 42, 79", "22, 22, 26")
content = content.replace("10, 116, 218", "139, 92, 246")
content = content.replace("13, 226, 255", "0, 245, 255")
content = content.replace("0, 5, 10", "4, 4, 6")
content = content.replace("Deep Aqua Liquid Theme", "Hyper-Premium Midnight Theme")

with open(r'c:\Users\admin\Desktop\cyber multiple accoun with DA and ACK\src\ui_styling.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated Theme")
