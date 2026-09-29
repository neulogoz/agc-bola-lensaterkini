import os
import random
import time
import requests
from google import genai
import json
import re
from datetime import datetime

print("=== MEMULAI SCRIPT AGC BOLA (POPUNDER FIX & SCOREAXIS ORIGINAL) ===")

API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    print("ERROR: GEMINI_API_KEYS tidak ditemukan!")
    raise ValueError("GEMINI_API_KEYS belum di-set di GitHub.")

API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]

# Pemisahan Sumber RSS
RSS_INT = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.espn.com/espn/rss/soccer/news"
]
RSS_LOKAL = [
    "https://www.bola.net/feed/",
    "https://www.suara.com/rss/bola"
]

OUTPUT_DIR = "public/berita"
os.makedirs(OUTPUT_DIR, exist_ok=True)
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg"

# =====================================================================
# WIDGET SCOREAXIS ASLI MILIK ANDA (TANPA MODIFIKASI)
# Jika masih 404, silakan ganti kode di bawah ini dengan widget baru dari ScoreAxis
# =====================================================================
WIDGET_ENG = """<div id="widget-atvlmumh1msi" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/6232265abf1fa71a672159ec?widgetId=atvlmumh1msi&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>"""
WIDGET_ESP = """<div id="widget-j7xwmumh3y7m" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62322c053617da0b83221cc6?widgetId=j7xwmumh3y7m&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>"""
WIDGET_ITA = """<div id="widget-llkdmumh65vu" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62322b827aee66235a2be718?widgetId=llkdmumh65vu&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>"""
WIDGET_GER = """<div id="widget-t6xvmumh55i6" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62321f50f7016c22d3650732?widgetId=t6xvmumh55i6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>"""
WIDGET_FRA = """<div id="widget-bjs9mumh5ta6" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62322b4efd209951602c9096?widgetId=bjs9mumh5ta6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>"""
WIDGET_IDN = """<div id="widget-wrt7mumh7146" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/623225c009ac1611ee0dc0f6?widgetId=wrt7mumh7146&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>"""

# =====================================================================
# SCRIPT IKLAN & HISTATS
# =====================================================================
SCRIPT_ADSTERRA_728 = """
<script>
  atOptions = {
    'key' : '70f7df03b8ac15936657a97b9d6d37f7',
    'format' : 'iframe',
    'height' : 90,
    'width' : 728,
    'params' : {}
  };
</script>
<script src="https://www.highrevenueformat.com/70f7df03b8ac15936657a97b9d6d37f7/invoke.js"></script>
"""

SCRIPT_ADSTERRA_300 = """
<script>
  atOptions = {
    'key' : '29f673e95ea974afd5b3ecb133ef6a9e',
    'format' : 'iframe',
    'height' : 250,
    'width' : 300,
    'params' : {}
  };
</script>
<script src="https://www.highrevenueformat.com/29f673e95ea974afd5b3ecb133ef6a9e/invoke.js"></script>
"""

# Pop-Under diberi tipe javascript & data-cfasync agar lolos dari pemblokir Cloudflare
SCRIPT_POPUNDER = """
<script type='text/javascript' src='//pl31570858.profitableratecpmnetwork.com/bf/7c/c8/bf7cc8b38eeb859ad03672bf296c81ba.js' data-cfasync='false'></script>
"""

SCRIPT_HISTATS = """
<!-- Histats.com  START  (aync)-->
<script type="text/javascript">var _Hasync= _Hasync|| [];
_Hasync.push(['Histats.start', '1,5055086,4,0,0,0,00010000']);
_Hasync.push(['Histats.fasi', '1']);
_Hasync.push(['Histats.track_hits', '']);
(function() {
var hs = document.createElement('script'); hs.type = 'text/javascript'; hs.async = true;
hs.src = ('//s10.histats.com/js15_as.js');
(document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(hs);
})();</script>
<noscript><a href="/" target="_blank"><img  src="//sstatic1.histats.com/0.gif?5055086&101" alt="frontpage hit counter" border="0"></a></noscript>
<!-- Histats.com  END  -->
"""

SCRIPT_PAGINATION_SEARCH = """
<script>
    function searchNews() {
        const input = document.getElementById('searchInput').value.toLowerCase();
        const cards = document.querySelectorAll('.news-card');
        
        if(input.length > 0) {
            document.querySelector('.pagination').style.display = 'none';
            cards.forEach(card => {
                if (card.getAttribute('data-title').includes(input)) {
                    card.style.display = 'grid';
                } else {
                    card.style.display = 'none';
                }
            });
        } else {
            document.querySelector('.pagination').style.display = 'flex';
            showPage(currentPage);
        }
    }

    const itemsPerPage = 5;
    let currentPage = 1;
    const articles = document.querySelectorAll('.news-card');
    const totalPages = Math.ceil(articles.length / itemsPerPage);

    function showPage(page) {
        if(document.getElementById('searchInput') && document.getElementById('searchInput').value.length > 0) return;
        
        articles.forEach((card, index) => {
            if (index >= (page - 1) * itemsPerPage && index < page * itemsPerPage) {
                card.style.display = 'grid';
            } else {
                card.style.display = 'none';
            }
        });
        if(document.getElementById('page-info')) document.getElementById('page-info').innerText = 'Halaman ' + page + ' dari ' + totalPages;
        if(document.getElementById('btn-prev')) document.getElementById('btn-prev').disabled = page === 1;
        if(document.getElementById('btn-next')) document.getElementById('btn-next').disabled = page === totalPages || totalPages === 0;
    }

    function changePage(delta) {
        currentPage += delta;
        showPage(currentPage);
        const newsSection = document.getElementById('berita-terbaru');
        if(newsSection) {
            newsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    if(articles.length > 0) showPage(1);
</script>
"""

def get_gemini_response(prompt):
    random.shuffle(API_KEYS_LIST)
    ai_models = ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    
    for current_key in API_KEYS_LIST:
        try:
            client = genai.Client(api_key=current_key)
            for model_name in ai_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    text = response.text
                    bt = chr(96) * 3 
                    text = re.sub(bt + r'html', '', text, flags=re.IGNORECASE)
                    text = text.replace(bt, '')
                    return text.strip()
                except Exception as model_err:
                    if "404" in str(model_err) or "not found" in str(model_err).lower():
                        continue 
                    else:
                        raise model_err 
        except Exception:
            time.sleep(2)
            continue
    return None

def generate_article_with_gemini(news_item):
    title = news_item.get('title', 'Berita Bola')
    description = news_item.get('description', '')
    
    thumbnail = ""
    if 'enclosure' in news_item and isinstance(news_item['enclosure'], dict):
        thumbnail = news_item['enclosure'].get('link', '')
    if not thumbnail and 'thumbnail' in news_item:
        thumbnail = news_item.get('thumbnail', '')
        
    if not thumbnail or not thumbnail.startswith('http'):
        thumbnail = "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800&auto=format&fit=crop"
    else:
        thumbnail = f"https://wsrv.nl/?url={thumbnail}&w=800&output=webp"
        
    prompt = f"""
    Bertindaklah sebagai jurnalis sepak bola profesional dari Indonesia. 
    Tulis ulang berita berikut menjadi artikel berita sepak bola berbahasa Indonesia (minimal 300 kata).
    
    Data Asli:
    - Judul: {title}
    - Ringkasan: {description}
    
    ATURAN FORMATTING (DILARANG MELANGGAR):
    1. Keluarkan HTML murni, tanpa simbol pagar atau bintang tebal.
    2. Baris pertama wajib: <h1>[Judul]</h1>
    3. Gunakan tag <p> untuk paragraf.
    4. Di baris paling bawah, tambahkan tag Kategori seperti ini:
       KATEGORI: LOKAL (jika berita bola Indonesia) 
       atau 
       KATEGORI: INTERNASIONAL (jika berita bola luar negeri/global).
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        article_content = article_content.replace('**', '') 
        article_content = re.sub(r'^#+\s*', '', article_content, flags=re.MULTILINE) 
        
        category = "INTERNASIONAL"
        if "KATEGORI: LOKAL" in article_content.upper():
            category = "LOKAL"
        article_content = re.sub(r'KATEGORI:\s*(LOKAL|INTERNASIONAL)', '', article_content, flags=re.IGNORECASE).strip()
        
        indo_title = title 
        title_match = re.search(r'<h1>(.*?)</h1>', article_content, re.IGNORECASE)
        if title_match:
            indo_title = title_match.group(1).strip()
            article_content = re.sub(r'<h1>.*?</h1>', '', article_content, count=1, flags=re.IGNORECASE)
            
        lines = article_content.split('\n')
        clean_html = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if not line.startswith('<'): line = f"<p>{line}</p>"
            clean_html.append(line)
        article_content = '\n'.join(clean_html)
        
        excerpt = "Berita sepak bola terbaru dan terhangat."
        p_match = re.search(r'<p>(.*?)</p>', article_content, re.IGNORECASE)
        if p_match:
            excerpt = re.sub(r'<[^>]+>', '', p_match.group(1))[:150] + "..."
            
        return article_content, indo_title, excerpt, thumbnail, category
    return None, None, None, None, None

def save_as_html(content, title, excerpt, thumbnail, category):
    slug = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    filename = f"{OUTPUT_DIR}/{slug}.html"
    timestamp = int(time.time())
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Lensa Terkini Bola</title>
        <meta name="description" content="{excerpt}">
        <meta name="publish-date" content="{timestamp}">
        <meta name="article-category" content="{category}">
        
        <!-- POPUNDER HARUS DI HEAD AGAR AKTIF SEJAK KLIK PERTAMA -->
        {SCRIPT_POPUNDER}
        
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Poppins', sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; color: #2c3e50; overflow-x: hidden; }}
            .container {{ max-width: 850px; margin: 40px auto; padding: 40px; background: #fff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
            
            header {{ background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: white; padding: 25px 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); border-bottom: 4px solid #e74c3c; }}
            .logo-wrap {{ display: inline-flex; align-items: center; justify-content: center; gap: 15px; text-decoration: none; color: white; }}
            .logo-icon {{ width: 50px; height: 50px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.4)); }}
            .site-title {{ font-size: 2.2em; font-weight: 700; letter-spacing: 1px; margin: 0; }}
            
            .badge-wrapper {{ text-align: center; margin: 20px 0; }}
            .badge-kategori {{ background: {'#e74c3c' if category == 'LOKAL' else '#00416A'}; color: white; padding: 6px 15px; border-radius: 20px; font-size: 0.9em; font-weight: 600; letter-spacing: 0.5px; display: inline-block; }}
            
            h1 {{ color: #0f2027; font-size: 2.4em; line-height: 1.3; margin: 10px 0 25px 0; font-weight: 700; text-align: center; }}
            .hero-img {{ width: 100%; max-height: 500px; object-fit: cover; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            
            .ad-slot {{ background: #f8f9fa; border: 1px dashed #ced4da; padding: 15px; text-align: center; margin: 30px 0; border-radius: 8px; overflow: hidden; }}
            p {{ line-height: 1.8; font-size: 1.15em; margin-bottom: 20px; color: #444; text-align: justify; }}
            
            .back-btn {{ display: block; width: max-content; margin: 30px auto 0; padding: 12px 25px; background: #00416A; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,65,106,0.2); }}
            .back-btn:hover {{ background: #002d4a; transform: translateY(-2px); }}
        </style>
    </head>
    <body>
        <header>
            <a href="/" class="logo-wrap">
                <img src="{LOGO_URL}" alt="Logo Bola" class="logo-icon">
                <h1 class="site-title">Lensa Terkini Bola</h1>
            </a>
        </header>
        
        <!-- Iklan Top -->
        <div class="ad-slot">
            {SCRIPT_ADSTERRA_728}
        </div>
        
        <div class="container">
            <div class="badge-wrapper"><span class="badge-kategori">{category}</span></div>
            
            <h1>{title}</h1>
            <img src="{thumbnail}" alt="{title}" class="hero-img" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1518605368461-1e1c071d3326?q=80&w=800&auto=format&fit=crop';">
            
            <article>{content}</article>
            
            <div class="ad-slot">
                {SCRIPT_ADSTERRA_300}
            </div>
            
            <a href="/" class="back-btn">⬅ Kembali ke Beranda</a>
        </div>

        <div style="display:none;">
            {SCRIPT_HISTATS}
        </div>
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)

def update_homepage():
    def get_meta(filepath, meta_name, default=""):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(fr'<meta name="{meta_name}" content="(.*?)">', content)
                return match.group(1) if match else default
        except: return default
        
    berita_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.html')]
    berita_files.sort(key=lambda x: int(get_meta(os.path.join(OUTPUT_DIR, x), "publish-date", "0")), reverse=True)
    
    daftar_artikel_html = ""
    for filename in berita_files:
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
                title = re.search(r'<title>(.*?)</title>', html_content).group(1).replace(' - Lensa Terkini Bola', '')
                excerpt = get_meta(filepath, "description", "Baca selengkapnya...")
                category = get_meta(filepath, "article-category", "INTERNASIONAL")
                img_match = re.search(r'<img src="(.*?)" alt=".*?" class="hero-img"', html_content)
                thumbnail = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1518605368461-1e1c071d3326?q=80&w=800"
                
                cat_color = "#e74c3c" if category == "LOKAL" else "#00416A"
                
                daftar_artikel_html += f'''
                <div class="news-card" data-title="{title.lower()}">
                    <img src="{thumbnail}" alt="Thumbnail Berita" class="news-thumb" loading="lazy" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800&auto=format&fit=crop';">
                    <div class="news-info">
                        <span class="news-badge" style="background:{cat_color};">{category}</span>
                        <h3><a href="/berita/{filename}">{title}</a></h3>
                        <p>{excerpt}</p>
                    </div>
                </div>\n'''
        except Exception:
            continue

    homepage_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lensa Terkini Bola - Portal Berita Sepak Bola</title>
        
        <!-- POPUNDER HARUS DI HEAD AGAR AKTIF SEJAK KLIK PERTAMA -->
        {SCRIPT_POPUNDER}
        
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
            
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Poppins', sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; color: #2c3e50; overflow-x: hidden; }}
            
            header {{ background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: white; padding: 40px 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); border-bottom: 4px solid #e74c3c; }}
            .logo-container {{ display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 12px; }}
            .header-logo {{ width: 60px; height: 60px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.4)); }}
            header h1 {{ margin: 0; font-size: 2.8em; font-weight: 700; letter-spacing: 1px; }}
            header p {{ margin: 5px 0 0 0; opacity: 0.8; font-size: 1.1em; }}
            
            .ad-slot {{ background: #fff; border: 1px dashed #ced4da; padding: 15px; text-align: center; margin: 20px auto; max-width: 1100px; border-radius: 8px; overflow: hidden; }}
            
            /* MEGA KLASEMEN (CAROUSEL / SCROLL HORIZONTAL) */
            .mega-standings-wrapper {{ max-width: 1250px; margin: 10px auto 30px auto; padding: 0 20px; }}
            .section-heading {{ font-size: 1.8em; color: #0f2027; border-left: 5px solid #e74c3c; padding-left: 15px; margin-bottom: 20px; font-weight: 700; display: flex; align-items: center; gap: 10px; }}
            
            .standings-grid {{ 
                display: flex; 
                flex-wrap: nowrap; 
                overflow-x: auto; 
                gap: 20px; 
                padding-bottom: 20px; 
                scroll-behavior: smooth;
                -webkit-overflow-scrolling: touch;
            }}
            
            .standings-box {{ 
                flex: 0 0 320px; 
                height: 480px; 
                background: #fff; 
                border-radius: 12px; 
                padding: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
                border: 1px solid #f0f0f0; 
                overflow-y: auto; 
            }}
            
            .standings-box h3 {{ text-align: center; margin: 0 0 15px 0; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; color: #00416A; font-size: 1.2em; }}
            
            .standings-grid::-webkit-scrollbar {{ height: 10px; }}
            .standings-grid::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 10px; }}
            .standings-grid::-webkit-scrollbar-thumb {{ background: #00416A; border-radius: 10px; }}
            .standings-grid::-webkit-scrollbar-thumb:hover {{ background: #e74c3c; }}
            .standings-box::-webkit-scrollbar {{ width: 5px; }}
            .standings-box::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 5px; }}
            
            /* BERITA DAN SIDEBAR BAWAH */
            .main-container {{ display: flex; flex-wrap: wrap; max-width: 1250px; margin: 40px auto; padding: 0 20px; gap: 35px; border-top: 2px dashed #ccc; padding-top: 40px; }}
            .content-left {{ flex: 1; min-width: 60%; }}
            .sidebar-right {{ width: 360px; flex-shrink: 0; }}
            
            .search-box {{ width: 100%; padding: 15px 25px; margin-bottom: 30px; border: 2px solid #e1e8ed; border-radius: 30px; font-size: 1.1em; font-family: inherit; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }}
            .search-box:focus {{ border-color: #00416A; outline: none; box-shadow: 0 4px 15px rgba(0,65,106,0.15); }}
            
            .news-card {{ display: grid; grid-template-columns: 240px 1fr; gap: 20px; background: #fff; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); transition: all 0.3s ease; border: 1px solid #f0f0f0; padding: 15px; }}
            .news-card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 25px rgba(0,0,0,0.08); border-color: #00416A; }}
            .news-thumb {{ width: 100%; height: 160px; object-fit: cover; border-radius: 8px; background-color: #eaeaea; }}
            .news-info {{ display: flex; flex-direction: column; justify-content: center; }}
            .news-badge {{ color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 600; align-self: flex-start; margin-bottom: 10px; }}
            .news-info h3 {{ margin: 0 0 10px 0; font-size: 1.25em; line-height: 1.4; }}
            .news-info a {{ text-decoration: none; color: #0f2027; transition: color 0.2s; }}
            .news-info a:hover {{ color: #e74c3c; }}
            .news-info p {{ margin: 0; color: #555; font-size: 0.95em; line-height: 1.6; }}
            
            .pagination {{ display: flex; justify-content: center; align-items: center; margin: 40px 0; gap: 15px; }}
            .pagination button {{ padding: 10px 25px; background: #00416A; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-family: inherit; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,65,106,0.2); }}
            .pagination button:hover:not(:disabled) {{ background: #002d4a; transform: translateY(-2px); }}
            .pagination button:disabled {{ background: #bdc3c7; cursor: not-allowed; box-shadow: none; }}
            .pagination span {{ font-weight: 600; }}
            
            .telegram-banner {{ background: linear-gradient(135deg, #1c92d2, #f2fcfe); border-radius: 12px; padding: 25px 20px; text-align: center; color: #0f2027; margin-bottom: 30px; box-shadow: 0 8px 20px rgba(28,146,210,0.15); position: relative; overflow: hidden; border: 1px solid rgba(255,255,255,0.5); }}
            .telegram-banner h3 {{ margin: 0 0 10px 0; font-size: 1.5em; font-weight: 700; }}
            .telegram-banner p {{ font-size: 0.95em; margin-bottom: 20px; color: #333; }}
            .btn-telegram {{ display: inline-block; background: #0088cc; color: #fff; padding: 12px 25px; border-radius: 30px; text-decoration: none; font-weight: 600; font-size: 1.1em; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,136,204,0.3); }}
            .btn-telegram:hover {{ transform: scale(1.05); background: #0077b3; }}
            
            @media (max-width: 900px) {{
                .main-container {{ flex-direction: column; }}
                .sidebar-right {{ width: 100%; }}
                .news-card {{ grid-template-columns: 1fr; }}
                .news-thumb {{ height: 200px; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo-container">
                <img src="{LOGO_URL}" alt="Logo Lensa Terkini" class="header-logo">
                <h1>Lensa Terkini Bola</h1>
            </div>
            <p>Portal Berita & Update Skor Bola Dunia</p>
        </header>

        <!-- IKLAN BANNER BESAR: Tepat di Bawah Header -->
        <div class="ad-slot">
            {SCRIPT_ADSTERRA_728}
        </div>

        <div class="mega-standings-wrapper">
            <h2 class="section-heading">🏆 PUSAT KLASEMEN LIGA DUNIA</h2>
            <p style="font-size: 0.9em; color: #7f8c8d; margin-top: -15px; margin-bottom: 15px; padding-left: 20px;">Geser ke kanan untuk melihat liga lainnya.</p>
            <div class="standings-grid">
                <div class="standings-box">
                    <h3>Liga Inggris</h3>
                    {WIDGET_ENG}
                </div>
                <div class="standings-box">
                    <h3>Liga Spanyol</h3>
                    {WIDGET_ESP}
                </div>
                <div class="standings-box">
                    <h3>Liga Italia</h3>
                    {WIDGET_ITA}
                </div>
                <div class="standings-box">
                    <h3>Liga Jerman</h3>
                    {WIDGET_GER}
                </div>
                <div class="standings-box">
                    <h3>Liga Prancis</h3>
                    {WIDGET_FRA}
                </div>
                <div class="standings-box">
                    <h3>Liga Indonesia</h3>
                    {WIDGET_IDN}
                </div>
            </div>
        </div>

        <div class="main-container" id="berita-terbaru">
            <div class="content-left">
                <h2 class="section-heading">📰 Berita Terbaru</h2>
                <input type="text" id="searchInput" class="search-box" placeholder="🔍 Cari berita klub atau liga di sini..." onkeyup="searchNews()">
                
                <div id="news-list">
                    {daftar_artikel_html}
                </div>
                
                <div class="pagination">
                    <button id="btn-prev" onclick="changePage(-1)">&#8592; Sebelumnya</button>
                    <span id="page-info">Halaman 1</span>
                    <button id="btn-next" onclick="changePage(1)">Selanjutnya &#8594;</button>
                </div>
            </div>

            <div class="sidebar-right">
                
                <div class="telegram-banner">
                    <h3>🔥 Nonton Bola Gratis!</h3>
                    <p>Gabung komunitas kami dan dapatkan link live streaming pertandingan bola terupdate setiap harinya tanpa bayar.</p>
                    <a href="#" class="btn-telegram" rel="nofollow noopener noreferrer">Tonton Sekarang ➔</a>
                </div>

                <div class="ad-slot">
                    {SCRIPT_ADSTERRA_300}
                </div>
            </div>
        </div>

        <div style="display:none;">
            {SCRIPT_HISTATS}
        </div>
        
        {SCRIPT_PAGINATION_SEARCH}

    </body>
    </html>
    """
    
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage_template)

def main():
    try:
        int_news = []
        lokal_news = []
        
        print("\nMengumpulkan berita Internasional...")
        for source in RSS_INT:
            try:
                res = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={source}", timeout=10)
                if 'items' in res.json(): int_news.extend(res.json()['items'])
            except: pass
            
        print("Mengumpulkan berita Lokal...")
        for source in RSS_LOKAL:
            try:
                res = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={source}", timeout=10)
                if 'items' in res.json(): lokal_news.extend(res.json()['items'])
            except: pass
                
        random.shuffle(int_news)
        random.shuffle(lokal_news)
        
        # JAMINAN KESEIMBANGAN: 3 Internasional, 2 Lokal
        final_news_batch = int_news[:3] + lokal_news[:2]
        random.shuffle(final_news_batch)
        
        if not final_news_batch:
            print("PERHATIAN: Tidak ada data berita.")
            return
            
        for item in final_news_batch: 
            content, title, excerpt, thumb, category = generate_article_with_gemini(item)
            if content:
                save_as_html(content, title, excerpt, thumb, category)
        
        update_homepage()
                
    except Exception as e:
        print(f"ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
