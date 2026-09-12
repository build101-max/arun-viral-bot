import os
import random
import requests
import textwrap
# Pillow is for making image
from PIL import Image, ImageDraw, ImageFont

# Step 1: List of subreddits where viral stories come from
SUBREDDITS = ['AmITheAsshole','confession','RelationshipIndia','AskIndia','indiasocial']

# Step 2: Function to make 1080x1350 image with text
def create_image(text):
    # Create white image 1080 width, 1350 height (instagram size)
    W, H = 1080, 1350
    img = Image.new('RGB', (W, H), color='white')
    draw = ImageDraw.Draw(img)

    # Try to load nice font, if not found use default
    try:
        # On GitHub Actions ubuntu, DejaVu font exists
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_footer = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # Add top heading
    draw.text((60, 60), "VIRAL CONFESSION", font=font_title, fill="black")

    # Wrap long text so it fits inside image
    wrapped_lines = textwrap.wrap(text, width=32)  # 32 chars per line
    y = 160
    for line in wrapped_lines[:18]:  # Max 18 lines so it fits
        draw.text((60, y), line, font=font_body, fill="#111111")
        y += 55

    # Add footer @arun56333 at bottom
    draw.rectangle([(0, H-80), (W, H)], fill="#0a0a0a")
    draw.text((60, H-60), "@arun56333  •  Viral Bot", font=font_footer, fill="white")

    # Save image
    path = "viral_post.jpg"
    img.save(path)
    print(f"Image created: {path}")
    return path

# Step 3: Function to send photo to Telegram
def send_telegram(photo_path, caption):
    # Get token and chat id from GitHub Secrets
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "7986889709")

    if not token:
        print("ERROR: TELEGRAM_TOKEN not found in secrets")
        return False

    # Telegram API url to send photo
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    try:
        # Open image and send
        with open(photo_path, 'rb') as photo:
            data = {
                'chat_id': chat_id,
                'caption': caption[:1000]  # Telegram caption limit
            }
            files = {'photo': photo}
            r = requests.post(url, data=data, files=files, timeout=30)
            print(f"Telegram response: {r.status_code} - {r.text[:200]}")
            return r.status_code == 200
    except Exception as e:
        print(f"Failed to send telegram: {e}")
        return False

# Step 4: Main function - runs only once (no infinite loop)
def main():
    try:
        print("Bot started - arun56333")

        # Shuffle subreddits so we get different content each time
        random.shuffle(SUBREDDITS)
        found_post = None

        # Go through each subreddit to find viral post
        for sub in SUBREDDITS:
            try:
                print(f"Checking r/{sub}...")
                # Reddit top posts of today
                url = f"https://www.reddit.com/r/{sub}/top.json?limit=10&t=day"
                headers = {'User-Agent': 'arun56333'}
                res = requests.get(url, headers=headers, timeout=15)
                
                if res.status_code != 200:
                    print(f"r/{sub} failed: {res.status_code}")
                    continue

                data = res.json()
                posts = data.get('data', {}).get('children', [])
                
                # Filter only posts with score > 5000 (viral)
                viral = [p['data'] for p in posts if p['data'].get('score', 0) > 5000]
                
                if viral:
                    # Pick random one from viral posts
                    found_post = random.choice(viral)
                    print(f"Found viral post from r/{sub}: {found_post['score']} upvotes")
                    break
                else:
                    print(f"No viral >5000 in r/{sub}, trying next")

            except Exception as e:
                print(f"Error in r/{sub}: {e}")
                continue

        # If no viral post found in all subreddits, take any top post
        if not found_post:
            print("No 5000+ score post, taking fallback")
            # Try again without filter
            for sub in SUBREDDITS:
                try:
                    url = f"https://www.reddit.com/r/{sub}/top.json?limit=10&t=day"
                    res = requests.get(url, headers={'User-Agent': 'arun56333'}, timeout=15)
                    posts = res.json().get('data', {}).get('children', [])
                    if posts:
                        found_post = random.choice(posts)['data']
                        break
                except:
                    continue

        if not found_post:
            print("No post found at all, exit")
            return

        # Get title and text
        title = found_post.get('title', 'Viral Story')
        selftext = found_post.get('selftext', '')[:600]  # Take first 600 chars
        full_text = f"{title}\n\n{selftext}" if selftext else title

        # Make image
        image_path = create_image(full_text)

        # Make caption for telegram
        caption = f"🔥 {title}\n\n👀 Score: {found_post.get('score')} upvotes\n\n@arun56333"

        # Send to telegram
        success = send_telegram(image_path, caption)
        
        if success:
            print("SUCCESS: Sent to Telegram!")
        else:
            print("FAILED to send")

    except Exception as e:
        print(f"Main error: {e}")

    # End - GitHub Actions will stop here, no while True
    print("Bot finished, exiting")
    exit()

# Run main
if __name__ == "__main__":
    main()
