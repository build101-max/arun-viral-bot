import os, requests, random, textwrap, time
from PIL import Image, ImageDraw, ImageFont

SUBREDDITS = ['indiasocial','RelationshipIndia','AskIndia','confession','AmITheAsshole','IndiaSpeaks']

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://old.reddit.com/"
}

def fetch_posts(sub):
    urls = [
        f"https://old.reddit.com/r/{sub}/top.json?limit=25&t=day",
        f"https://www.reddit.com/r/{sub}/top.json?limit=25&t=day",
        f"https://api.reddit.com/r/{sub}/top.json?limit=25&t=day"
    ]
    for url in urls:
        try:
            print(f"Checking r/{sub} via {url}...")
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                children = data.get('data', {}).get('children', [])
                if children:
                    print(f"Got {len(children)} posts from r/{sub}")
                    return children
            else:
                print(f"r/{sub} failed: {r.status_code} on {url}")
        except Exception as e:
            print(f"r/{sub} error on {url}: {e}")
        time.sleep(1)
    return []

def create_image(text, path="/tmp/post.jpg"):
    W,H = 1080,1350
    img = Image.new('RGB',(W,H),color=(255,255,255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font = ImageFont.load_default()
        small = font
    wrapped = textwrap.fill(text, width=38)
    # card
    draw.rectangle([40,40,W-40,H-120], fill=(250,250,250), outline=(220,220,220), width=2)
    draw.text((70,80), wrapped, fill=(20,20,20), font=font, spacing=12)
    draw.text((70,H-80), "@arun56333 | Viral Reddit", fill=(100,100,100), font=small)
    img.save(path, quality=95)
    return path

def send_telegram(photo_path, caption):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing TELEGRAM_TOKEN or CHAT_ID secrets!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path,'rb') as f:
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1000]}
        files = {"photo": f}
        r = requests.post(url, data=data, files=files, timeout=20)
        print(f"Telegram response: {r.status_code} {r.text[:500]}")
        if r.status_code == 200:
            print("✅ SENT TO TELEGRAM!")

def main():
    print("Bot started - arun56333 - 403 fixed version")
    all_posts = []
    for sub in SUBREDDITS:
        posts = fetch_posts(sub)
        for p in posts:
            d = p['data']
            if not d.get('is_video') and d.get('selftext'):
                all_posts.append(d)
        if all_posts and len(all_posts) >= 20:
            break
        time.sleep(1)
    
    if not all_posts:
        print("No post found at all, exit")
        return
    
    # pick best by score, but fallback to any if no high score
    all_posts.sort(key=lambda x: x.get('score',0), reverse=True)
    best = None
    for post in all_posts:
        if post.get('score',0) > 200:
            best = post
            break
    if not best:
        best = all_posts[0]
    
    title = best.get('title','')
    selftext = best.get('selftext','')[:600]
    full = f"{title}\n\n{selftext}"
    
    print(f"Selected: {title[:80]} | Score: {best.get('score')}")
    img_path = create_image(full)
    caption = f"{title[:900]}\n\nvia r/{best.get('subreddit')} | @arun56333"
    send_telegram(img_path, caption)

if __name__ == "__main__":
    main()
