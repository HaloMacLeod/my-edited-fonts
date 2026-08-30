import json
import urllib.parse
import subprocess
import sys

def get_valid_url(prompt_text: str, optional: bool = False) -> str:
    """Prompts the user for a URL or allows typing 'n' to skip if optional."""
    while True:
        user_input = input(prompt_text).strip()
        
        if optional and user_input.lower() == 'n':
            return ""
        
        if user_input.startswith("http://") or user_input.startswith("https://"):
            return user_input
        
        if optional:
            print("❌ Invalid entry. Enter a valid http(s):// link or 'n'.")
        else:
            print("❌ Invalid URL. Enter a valid link starting with http(s)://.")

def push_to_github():
    """Commits and pushes font.json using the local Git CLI."""
    try:
        print("\n--- Pushing to GitHub ---")
        subprocess.run(["git", "add", "font.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Update font.json for Revenge Discord"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✓ Successfully pushed 'font.json' to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed: {e}")
        print("Ensure you are running this inside a git repo connected to GitHub.")

def main():
    print("--- Revenge Discord Font Generator & GitHub Uploader ---")
    
    # 1. Prompts for URLs
    main_url = get_valid_url("Enter Regular/Main raw .otf URL: ", optional=False)
    bold_url = get_valid_url("Enter Bold raw .otf URL (or type 'n' for none): ", optional=True)
    italic_url = get_valid_url("Enter Italic raw .otf URL (or type 'n' for none): ", optional=True)
    bold_italic_url = get_valid_url("Enter Bold-Italic raw .otf URL (or type 'n' for none): ", optional=True)
    
    # 2. Font display name prompt
    font_name = input("Enter Font Display Name: ").strip()
    while not font_name:
        font_name = input("Display name cannot be blank. Enter Font Display Name: ").strip()

    # Build json structure
    font_config = {
        "name": font_name,
        "main": main_url,
        "bold": bold_url if bold_url else main_url,
        "italic": italic_url if italic_url else main_url,
        "boldItalic": bold_italic_url if bold_italic_url else (bold_url if bold_url else main_url)
    }

    # Save font.json locally
    with open("font.json", "w", encoding="utf-8") as f:
        json.dump(font_config, f, indent=2)
    print("\n✓ Saved 'font.json' locally.")

    # 3. Ask to upload to GitHub
    upload_choice = input("Do you want to commit and push 'font.json' to GitHub now? (y/n): ").strip().lower()
    if upload_choice == 'y':
        push_to_github()

    # 4. Direct data-URI link fallback
    json_str = json.dumps(font_config, separators=(',', ':'))
    encoded_json = urllib.parse.quote(json_str)
    data_url = f"data:application/json,{encoded_json}"

    print("\n--- REVENGE DISCORD FONT LINK ---")
    print(data_url)
    print("---------------------------------")
    print("\nYou can also paste the 'data:application/json...' link directly into Revenge without waiting for GitHub.")

if __name__ == "__main__":
    main()
