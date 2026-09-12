import os, requests, textwrap, time, urllib.parse
from PIL import Image, ImageDraw, ImageFont

SUBREDDITS = ['indiasocial','RelationshipIndia','AskIndia','confession','AmITheAsshole','IndiaSpeaks']
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def fetch_posts(sub):
    target = f"https://old.reddit.com/r/{sub}/top.json?limit=25&t=day"
    encoded = urllib.parse.quote(target, safe='')
    urls = [
        target,
        f"https://api.allorigins.win/raw?url={encoded}",
        f"https://api.reddit.com/r/{sub}/top?t=day&limit=25"
    ]
    for url in urls:
        try:
            print(f"Checking r/{sub} via {url[:80]}...")
            r = requests.get(url, headers=HEADERS, timeout=20)
            print(f"Status: {r.status_code}")
            if r.status_code == 200 and 'data' in r.text:
                data = r.json()
                children = data.get('data', {}).get('children', [])
                if children:
                    print(f"✅ Got {len(children)} posts from r/{sub}")
                    return children
        except Exception as e:
            print(f"Error {e}")
        time.sleep(1)
    print(f"❌ All failed for r/{sub}")
    return []

def create_image(text, path="/tmp/post.jpg"):
    W,H = 1080,1350
    img = Image.new('RGB',(W,H), color=(255,255,255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font = ImageFont.load_default()
        small = font
    wrapped = textwrap.fill(text, width=38)
    draw.rectangle([40,40,W-40,H-120], fill=(250,250,250), outline=(200,200,200), width=2)
    draw.text((70,80), wrapped, fill=(20,20,20), font=font, spacing=12)
    draw.text((70,H-80), "@arun56333 | Viral Reddit", fill=(100,100,100), font=small)
    img.save(path, quality=95)
    return path

def send_telegram(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path,'rb') as f:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1000]}, files={"photo": f}, timeout=20)
        print(f"Telegram response: {r.status_code} {r.text[:500]}")
        if r.status_code == 200:
            print("✅✅✅ SENT TO TELEGRAM!")

def main():
    print("Bot started - arun56333 - FINAL PROXY FIX")
    all_posts = []
    for sub in SUBREDDITS:
        posts = fetch_posts(sub)
        for p in posts:
            d = p['data']
            if d.get('selftext'):
                all_posts.append(d)
        if len(all_posts) >= 10:
            break
    if not all_posts:
        print("No post found at all, exit")
        return
    all_posts.sort(key=lambda x: x.get('score',0), reverse=True)
    best = all_posts[0]
    full = f"{best.get('title','')}\n\n{best.get('selftext','')[:600]}"
    print(f"Selected: {full[:100]} | Score: {best.get('score')}")
    img = create_image(full)
    send_telegram(img, f"{best.get('title','')[:900]}\n\nvia r/{best.get('subreddit')} | @arun56333")

if __name__ == "__main__":
    main()
