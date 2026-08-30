import sys
import os
import math
import random
from fontTools.ttLib import TTFont
from fontTools.colorLib.builder import buildCOLR, buildCPAL

# Define trans flag colors as normalized floats (0.0 to 1.0)
TRANS_FLAG_COLORS = [
    (0x55 / 255.0, 0xCD / 255.0, 0xFC / 255.0, 1.0),  # Light Blue
    (0xF7 / 255.0, 0xA8 / 255.0, 0xB8 / 255.0, 1.0),  # Pink
    (1.0,          1.0,          1.0,          1.0),  # White
    (0xF7 / 255.0, 0xA8 / 255.0, 0xB8 / 255.0, 1.0),  # Pink
    (0x55 / 255.0, 0xCD / 255.0, 0xFC / 255.0, 1.0),  # Light Blue
]

def get_rotated_gradient_points(angle_deg, radius=500, center_x=350, center_y=450):
    """Calculates start and end coordinates for a linear gradient vector."""
    angle_rad = math.radians(angle_deg)
    dx = radius * math.cos(angle_rad)
    dy = radius * math.sin(angle_rad)
    
    p0x = int(center_x - dx)
    p0y = int(center_y - dy)
    p1x = int(center_x + dx)
    p1y = int(center_y + dy)
    
    return (p0x, p0y), (p1x, p1y)

def create_color_font(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    font = TTFont(input_path)
    glyph_order = font.getGlyphOrder()

    # 1. Prepare CPAL Palette
    palettes = [TRANS_FLAG_COLORS]

    # 2. Build COLR v1 Paint Graph
    target_glyphs = [g for g in glyph_order if g not in ['.notdef', '.null', 'nonmarkingreturn', 'space']]
    stop_positions = [0.0, 0.25, 0.5, 0.75, 1.0]

    color_glyphs = {}

    print(f"Randomizing trans flag gradient rotation for {len(target_glyphs)} characters...")

    for glyph_name in target_glyphs:
        random_angle = random.uniform(0, 360)
        (p0x, p0y), (p1x, p1y) = get_rotated_gradient_points(random_angle, radius=500, center_x=350, center_y=450)

        stops = [
            (pos, idx, 1.0)
            for idx, pos in enumerate(stop_positions)
        ]

        p2x = p0x - (p1y - p0y)
        p2y = p0y + (p1x - p0x)

        gradient_paint = {
            "Format": 4,  # PaintLinearGradient
            "ColorLine": {
                "Extend": "pad",
                "ColorStop": stops
            },
            "x0": p0x, "y0": p0y,
            "x1": p1x, "y1": p1y,
            "x2": p2x, "y2": p2y
        }

        glyph_paint = {
            "Format": 10,  # PaintGlyph
            "Paint": gradient_paint,
            "Glyph": glyph_name
        }

        color_glyphs[glyph_name] = glyph_paint

    # 3. Build & Attach Tables using colorLib Builders
    font["CPAL"] = buildCPAL(palettes)
    font["COLR"] = buildCOLR(color_glyphs, version=1)

    font.save(output_path)
    print(f"Success! Output color font saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    elif len(sys.argv) == 2:
        input_file = sys.argv[1]
        output_file = "output_colored.otf"
    else:
        input_file = "input.otf"
        output_file = "mc_sweetie_trans_pride_colored.otf"
    
    create_color_font(input_file, output_file)
