import json
import urllib.parse
import subprocess
import os
import glob
import math
import random
import re

# Try importing fonttools for Termux scaling and COLR/CPAL colorization
try:
    from fontTools.ttLib import TTFont
    from fontTools.colorLib.builder import buildCOLR, buildCPAL
    HAS_FONTTOOLS = True
except ImportError:
    HAS_FONTTOOLS = False

# Trans flag colors as normalized floats (0.0 to 1.0)
TRANS_FLAG_COLORS = [
    (0x55 / 255.0, 0xCD / 255.0, 0xFC / 255.0, 1.0),  # Light Blue
    (0xF7 / 255.0, 0xA8 / 255.0, 0xB8 / 255.0, 1.0),  # Pink
    (1.0,          1.0,          1.0,          1.0),  # White
    (0xF7 / 255.0, 0xA8 / 255.0, 0xB8 / 255.0, 1.0),  # Pink
    (0x55 / 255.0, 0xCD / 255.0, 0xFC / 255.0, 1.0),  # Light Blue
]

# Setup tab-completion for local files
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None

def local_otf_completer(text, state):
    """Autocompletes local .otf and .ttf files when hitting Tab."""
    files = glob.glob(f"{text}*.otf") + glob.glob(f"{text}*.ttf")
    if state < len(files):
        return files[state]
    return None

def setup_tab_autocompletion():
    """Hooks the completer function to readline."""
    if readline:
        readline.set_completer(local_otf_completer)
        readline.parse_and_bind("tab: complete")

def get_git_remote_info():
    """Detects GitHub username, repository name, and main branch from local git config."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], 
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        
        cleaned_url = remote_url.replace("git@github.com:", "").replace("https://github.com/", "")
        if cleaned_url.endswith(".git"):
            cleaned_url = cleaned_url[:-4]
        
        user_repo = cleaned_url.split("/")
        user, repo = user_repo[0], user_repo[1]

        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], 
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if not branch:
            branch = "main"

        return user, repo, branch
    except Exception:
        return None, None, None

def clean_string(text: str) -> str:
    """Strips all special characters and spaces, returning lowercase alphanumeric string."""
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def find_font_variants(base_filename: str) -> dict:
    """Case-insensitive search stripping special chars for matching bold/italic variants."""
    base, ext = os.path.splitext(base_filename)
    clean_input_base = clean_string(base)

    # Clean out common variant keywords from the base name to find the core font name
    core_name = clean_input_base
    for keyword in ["bolditalic", "italicbold", "regular", "bold", "italic", "oblique"]:
        core_name = core_name.replace(keyword, "")

    variants = {
        "regular": base_filename,
        "bold": None,
        "italic": None,
        "bold_italic": None
    }

    # Scan directory for all font files
    dir_files = glob.glob("*.otf") + glob.glob("*.ttf")

    for file in dir_files:
        f_base, f_ext = os.path.splitext(file)
        clean_f_base = clean_string(f_base)

        # Ensure the file belongs to the same font family
        if core_name in clean_f_base:
            has_bold = "bold" in clean_f_base
            has_italic = "italic" in clean_f_base or "oblique" in clean_f_base

            if has_bold and has_italic:
                variants["bold_italic"] = file
            elif has_bold:
                variants["bold"] = file
            elif has_italic:
                variants["italic"] = file
            elif "regular" in clean_f_base or clean_f_base == core_name:
                variants["regular"] = file

    return variants

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

def create_color_font(font: TTFont, input_filename: str) -> str:
    """Applies COLR v1/CPAL randomized Trans pride flag gradients to glyphs."""
    print(f"  🎨 Applying Trans Pride gradient to '{input_filename}'...")
    
    glyph_order = font.getGlyphOrder()
    palettes = [TRANS_FLAG_COLORS]
    target_glyphs = [g for g in glyph_order if g not in ['.notdef', '.null', 'nonmarkingreturn', 'space']]
    stop_positions = [0.0, 0.25, 0.5, 0.75, 1.0]

    color_glyphs = {}

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

    font["CPAL"] = buildCPAL(palettes)
    font["COLR"] = buildCOLR(color_glyphs, version=1)
    
    base, ext = os.path.splitext(input_filename)
    colored_filename = f"{base}_trans_colored{ext}"
    font.save(colored_filename)
    print(f"  ✓ Saved colored font as: {colored_filename}")
    return colored_filename

def scale_font_file(font: TTFont, filename: str, percent_increase: float) -> str:
    """Scales visible font size by adjusting global UPM and line metrics safely."""
    scale_factor = 1.0 + (percent_increase / 100.0)
    print(f"  🔍 Scaling '{filename}' up by {percent_increase}% (factor: {scale_factor:.2f})...")

    if "head" in font:
        font["head"].unitsPerEm = int(round(font["head"].unitsPerEm / scale_factor))

    if "hhea" in font:
        font["hhea"].ascent = int(round(font["hhea"].ascent / scale_factor))
        font["hhea"].descent = int(round(font["hhea"].descent / scale_factor))
        font["hhea"].lineGap = int(round(font["hhea"].lineGap / scale_factor))

    if "OS/2" in font:
        os2 = font["OS/2"]
        os2.sTypoAscender = int(round(os2.sTypoAscender / scale_factor))
        os2.sTypoDescender = int(round(os2.sTypoDescender / scale_factor))
        os2.sTypoLineGap = int(round(os2.sTypoLineGap / scale_factor))
        os2.usWinAscent = int(round(os2.usWinAscent / scale_factor))
        os2.usWinDescent = int(round(os2.usWinDescent / scale_factor))

    base, ext = os.path.splitext(filename)
    scaled_filename = f"{base}_scaled_{int(percent_increase)}pct{ext}"
    font.save(scaled_filename)

    print(f"  ✓ Saved scaled font as: {scaled_filename}")
    return scaled_filename

def process_single_font(filename: str, do_color: bool, percent_val: float) -> str:
    """Applies color and/or scaling to a single font file."""
    if not HAS_FONTTOOLS or not filename:
        return filename

    font = TTFont(filename)
    
    if do_color:
        filename = create_color_font(font, filename)
        font = TTFont(filename)

    if percent_val > 0:
        filename = scale_font_file(font, filename, percent_val)

    return filename

def prompt_and_process_fonts(user: str, repo: str, branch: str) -> tuple[dict, list]:
    """Prompts for input, detects variants, applies modifications, and builds GitHub URLs."""
    setup_tab_autocompletion()
    while True:
        filename = input("Enter .otf filename: ").strip()
        if filename:
            if not filename.endswith(".otf") and not filename.endswith(".ttf"):
                filename += ".otf"
            
            if not os.path.exists(filename):
                print(f"❌ File '{filename}' not found locally.")
                continue

            # Case-insensitive variant lookup
            detected_variants = find_font_variants(filename)
            print("\n🔎 Detected Font Variants in Directory:")
            print(f"  • Regular:     {detected_variants['regular']}")
            print(f"  • Bold:        {detected_variants['bold'] or 'Not found (will fallback to Regular)'}")
            print(f"  • Italic:      {detected_variants['italic'] or 'Not found (will fallback to Regular)'}")
            print(f"  • Bold-Italic: {detected_variants['bold_italic'] or 'Not found (will fallback to Bold/Italic)'}")

            # Colorize Prompt
            do_color = False
            if HAS_FONTTOOLS:
                color_choice = input("\nDo you want to apply Trans Flag COLR v1 gradient colors? (y/n): ").strip().lower()
                do_color = (color_choice == 'y')

            # Scaling Prompt
            percent_val = 0.0
            if HAS_FONTTOOLS:
                scale_choice = input("\nDo you want to scale up the font size? (y/n): ").strip().lower()
                if scale_choice == 'y':
                    percent_input = input("Enter percentage to scale up by [default: 25]: ").strip()
                    try:
                        percent_val = float(percent_input) if percent_input else 25.0
                    except ValueError:
                        print("⚠️ Invalid percentage entered. Defaulting to 25%.")
                        percent_val = 25.0

            # Process all detected font files
            processed_variants = {}
            modified_files = []

            for key, font_path in detected_variants.items():
                if font_path:
                    print(f"\nProcessing [{key.upper()}] variant...")
                    final_path = process_single_font(font_path, do_color, percent_val)
                    processed_variants[key] = final_path
                    modified_files.append(final_path)

            # Map GitHub Raw URLs
            raw_urls = {}
            for key, font_path in processed_variants.items():
                if font_path:
                    raw_urls[key] = f"https://github.com/{user}/{repo}/raw/{branch}/{font_path}?raw=1"

            # Assign fallbacks for missing variants
            reg_url = raw_urls["regular"]
            bold_url = raw_urls.get("bold") or reg_url
            italic_url = raw_urls.get("italic") or reg_url
            bold_italic_url = raw_urls.get("bold_italic") or bold_url

            urls_map = {
                "regular": reg_url,
                "bold": bold_url,
                "italic": italic_url,
                "bold_italic": bold_italic_url
            }

            return urls_map, modified_files
        print("❌ Filename cannot be empty.")

def push_to_github(files_to_push: list):
    """Commits and pushes specified files to GitHub using Git CLI."""
    try:
        print(f"\n--- Pushing to GitHub ---")
        for file in files_to_push:
            if os.path.exists(file):
                subprocess.run(["git", "add", file], check=True)
        
        subprocess.run(["git", "commit", "-m", "Generate Revenge Discord font variants with Spec:1 config"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✓ Successfully pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")

def main():
    print("--- Revenge Discord Font Suite (Auto Variant Detection) ---")
    
    user, repo, branch = get_git_remote_info()
    if not user or not repo:
        print("❌ Could not detect local Git repository connected to GitHub.")
        return
    
    print(f"✓ Detected Repo: {user}/{repo} (Branch: {branch})\n")

    # 1. Output JSON Filename
    raw_name = input("Enter output JSON filename (e.g., 'DearheartTransified'): ").strip()
    while not raw_name:
        raw_name = input("Filename cannot be blank: ").strip()

    base_json_name = raw_name[:-5] if raw_name.lower().endswith(".json") else raw_name
    json_filename = f"{base_json_name}.json"

    # 2. OTF Filename Prompt (With Auto-Variant Scanner)
    print("\n💡 Tip: Start typing your local file name and press [TAB] to autocomplete.")
    urls_map, files_to_commit = prompt_and_process_fonts(user, repo, branch)

    # 3. Font Display Name Prompt
    name_input = input(f"\nEnter Font Display Name [default: '{base_json_name}']: ").strip()
    font_name = name_input if name_input else base_json_name

    # PostScript Key Map targeting Regular, Bold, Medium/Italic variants
    main_mapping = {
        # Regular / Normal keys
        "ggsans-Normal": urls_map["regular"],
        "NotoSans-Normal": urls_map["regular"],
        
        # Medium / Semibold keys (Mapped to Italic if present, otherwise Regular)
        "ggsans-Medium": urls_map["italic"],
        "ggsans-Semibold": urls_map["italic"],
        "NotoSans-Medium": urls_map["italic"],
        "NotoSans-Semibold": urls_map["italic"],
        "SourceCodePro-Semibold": urls_map["italic"],

        # Bold keys
        "ggsans-Bold": urls_map["bold"],
        "NotoSans-Bold": urls_map["bold"],
        "ABCGintoNord-ExtraBold": urls_map["bold_italic"],
        "ggsans-ExtraBold": urls_map["bold_italic"],
        "NotoSans-ExtraBold": urls_map["bold_italic"],
    }

    # Spec 1 JSON Configuration
    font_config = {
        "spec": 1,
        "name": font_name,
        "previewText": font_name,
        "main": main_mapping
    }

    # Save JSON locally
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(font_config, f, indent=4)
    print(f"\n✓ Saved '{json_filename}' locally.")

    files_to_commit.append(json_filename)

    # 4. Push JSON and OTF files to GitHub
    upload_choice = input(f"\nPush config and all processed font files to GitHub now? (y/n): ").strip().lower()
    if upload_choice == 'y':
        push_to_github(files_to_commit)

    # 5. Output raw JSON link
    raw_json_link = f"https://github.com/{user}/{repo}/raw/{branch}/{json_filename}?raw=1"
    print("\n--- REVENGE DISCORD FONT IMPORT LINK ---")
    print(f"Paste this link under 'Import font entries from a link':\n{raw_json_link}")
    print("----------------------------------------")

if __name__ == "__main__":
    main()
