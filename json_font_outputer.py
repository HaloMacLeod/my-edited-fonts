import json
import urllib.parse
import subprocess
import os
import glob

# Try importing fonttools for Termux font scaling
try:
    from fontTools.ttLib import TTFont
    HAS_FONTTOOLS = True
except ImportError:
    HAS_FONTTOOLS = False

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

def scale_font_file(filename: str, percent_increase: float):
    """Scales visible font size by adjusting global UPM and line metrics safely."""
    if not HAS_FONTTOOLS:
        print("⚠️  fonttools module not found. Run 'pip install fonttools' in Termux.")
        return filename

    scale_factor = 1.0 + (percent_increase / 100.0)
    print(f"\n🔍 Scaling font '{filename}' up by {percent_increase}% (factor: {scale_factor:.2f}) using UPM adjustment...")
    
    font = TTFont(filename)

    # 1. Scale relative grid size via unitsPerEm (UPM)
    if "head" in font:
        font["head"].unitsPerEm = int(round(font["head"].unitsPerEm / scale_factor))

    # 2. Adjust vertical line metrics to maintain layout spacing
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

    # 3. Save scaled font file
    base, ext = os.path.splitext(filename)
    scaled_filename = f"{base}_scaled_{int(percent_increase)}pct{ext}"
    font.save(scaled_filename)

    print(f"✓ Saved scaled font as: {scaled_filename}")
    return scaled_filename

def prompt_otf_file(prompt_text: str, user: str, repo: str, branch: str) -> tuple[str, str]:
    """Prompts for an .otf file name with Tab autocomplete support and custom percentage scaling."""
    setup_tab_autocompletion()
    while True:
        filename = input(prompt_text).strip()
        if filename:
            if not filename.endswith(".otf") and not filename.endswith(".ttf"):
                filename += ".otf"
            
            if not os.path.exists(filename):
                print(f"❌ File '{filename}' not found locally.")
                continue

            # Scale prompt asking for specific percentage
            do_scale = input("\nDo you want to scale up the font size? (y/n): ").strip().lower()
            if do_scale == 'y':
                percent_input = input("Enter percentage to scale up by (e.g. '25' for 25% larger) [default: 25]: ").strip()
                try:
                    percent_val = float(percent_input) if percent_input else 25.0
                except ValueError:
                    print("⚠️ Invalid percentage entered. Defaulting to 25%.")
                    percent_val = 25.0
                
                filename = scale_font_file(filename, percent_val)

            raw_url = f"https://github.com/{user}/{repo}/raw/{branch}/{filename}?raw=1"
            print(f"  → Resolved URL: {raw_url}")
            return filename, raw_url
        print("❌ Filename cannot be empty.")

def push_to_github(files_to_push: list):
    """Commits and pushes specified files to GitHub using Git CLI."""
    try:
        print(f"\n--- Pushing to GitHub ---")
        for file in files_to_push:
            subprocess.run(["git", "add", file], check=True)
        
        subprocess.run(["git", "commit", "-m", "Generate scaled Revenge font with Spec:1 config"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✓ Successfully pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")

def main():
    print("--- Revenge Discord Font Generator (Termux fonttools Scaler) ---")
    
    user, repo, branch = get_git_remote_info()
    if not user or not repo:
        print("❌ Could not detect local Git repository connected to GitHub.")
        return
    
    print(f"✓ Detected Repo: {user}/{repo} (Branch: {branch})\n")

    # 1. Output JSON Filename
    raw_name = input("Enter output JSON filename (e.g., 'DearheartTransified'): ").strip()
    while not raw_name:
        raw_name = input("Filename cannot be blank: ").strip()

    # Clean the filename for the config name (strip .json if user manually typed it)
    base_json_name = raw_name[:-5] if raw_name.lower().endswith(".json") else raw_name
    json_filename = f"{base_json_name}.json"

    # 2. OTF Filename Prompt
    print("\n💡 Tip: Start typing your local file name and press [TAB] to autocomplete.")
    otf_filename, otf_url = prompt_otf_file("Enter .otf filename: ", user, repo, branch)

    # 3. Font Display Name / Preview Text (Defaults to the base JSON filename)
    name_input = input(f"\nEnter Font Display Name [default: '{base_json_name}']: ").strip()
    font_name = name_input if name_input else base_json_name

    # Standard Discord PostScript Key Map
    discord_postscript_keys = [
        "ABCGintoNord-ExtraBold",
        "ggsans-Bold",
        "ggsans-ExtraBold",
        "ggsans-Medium",
        "ggsans-Normal",
        "ggsans-Semibold",
        "NotoSans-Bold",
        "NotoSans-ExtraBold",
        "NotoSans-Medium",
        "NotoSans-Normal",
        "NotoSans-Semibold",
        "SourceCodePro-Semibold"
    ]

    main_mapping = {key: otf_url for key in discord_postscript_keys}

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

    # 4. Push JSON and OTF file to GitHub
    upload_choice = input(f"\nPush '{json_filename}' and '{otf_filename}' to GitHub now? (y/n): ").strip().lower()
    if upload_choice == 'y':
        files_to_commit = [json_filename]
        if os.path.exists(otf_filename):
            files_to_commit.append(otf_filename)
        push_to_github(files_to_commit)

    # 5. Output raw JSON link
    raw_json_link = f"https://github.com/{user}/{repo}/raw/{branch}/{json_filename}?raw=1"
    print("\n--- REVENGE DISCORD FONT IMPORT LINK ---")
    print(f"Paste this link under 'Import font entries from a link':\n{raw_json_link}")
    print("----------------------------------------")

if __name__ == "__main__":
    main()