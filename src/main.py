import os
import random
import time
import requests
from google import genai
import json
import re
from datetime import datetime

print("=== MEMULAI SCRIPT AGC BOLA (SEARCH, KATEGORI, TELEGRAM, ADS & HISTATS) ===")

API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    print("ERROR: GEMINI_API_KEYS tidak ditemukan!")
    raise ValueError("GEMINI_API_KEYS belum di-set di GitHub.")

API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]

RSS_SOURCES = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.bola.net/feed/",
    "https://www.suara.com/rss/bola"
]

OUTPUT_DIR = "public/berita"
os.makedirs(OUTPUT_DIR, exist_ok=True)
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg"

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
                    text = re.sub(r'```html', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'```', '', text)
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
    1. Keluarkan HTML murni, tanpa Markdown (# atau **).
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
        
        # Ekstrak Kategori
        category = "INTERNASIONAL"
        if "KATEGORI: LOKAL" in article_content.upper():
            category = "LOKAL"
        # Hapus teks kategori agar tidak tampil jelek di artikel
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
        
        <!-- RUANG IKLAN POP-UNDER ADSTERRA (HEADER) -->
        <!-- Paste script pop-under Anda di bawah ini -->
    
        
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; background: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            header {{ border-bottom: 2px solid #1a5276; margin-bottom: 20px; padding-bottom: 10px; display: flex; align-items: center; gap: 15px; justify-content: space-between; }}
            .logo-wrap {{ display: flex; align-items: center; gap: 15px; }}
            .logo-icon {{ width: 45px; height: 45px; }}
            .site-title {{ color: #1a5276; font-size: 1.6em; font-weight: bold; text-decoration: none; }}
            .badge-kategori {{ background: {'#e74c3c' if category == 'LOKAL' else '#2980b9'}; color: white; padding: 5px 12px; border-radius: 15px; font-size: 0.85em; font-weight: bold; }}
            h1 {{ color: #1a5276; font-size: 2.2em; line-height: 1.3; margin-top: 10px; }}
            .hero-img {{ width: 100%; max-height: 450px; object-fit: cover; border-radius: 8px; margin-bottom: 20px; background-color: #eaeaea; }}
            .ad-slot {{ background: #eaeaea; border: 1px dashed #bbb; padding: 15px; text-align: center; margin: 20px 0; color: #777; font-weight: bold; }}
            p {{ line-height: 1.8; font-size: 1.1em; margin-bottom: 15px; text-align: justify; }}
            .back-btn {{ display: inline-block; padding: 12px 20px; background: #1a5276; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="logo-wrap">
                    <img src="{LOGO_URL}" alt="Logo Bola" class="logo-icon">
                    <a href="/" class="site-title">Lensa Terkini</a>
                </div>
                <span class="badge-kategori">{category}</span>
            </header>
            
            <h1>{title}</h1>
            <img src="{thumbnail}" alt="{title}" class="hero-img" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1518605368461-1e1c071d3326?q=80&w=800&auto=format&fit=crop';">
            
            <div class="ad-slot">Space Iklan Adsterra 728x90</div>
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
            <article>{content}</article>
            <div class="ad-slot">Space Iklan Adsterra 300x250</div>
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
            
            <a href="/" class="back-btn">Kembali ke Beranda</a>
        </div>

        <!-- RUANG TRACKER HISTATS (HIDDEN) -->
        <div style="display:none;">
            <!-- Paste script Histats Anda di sini -->
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
                
                cat_color = "#e74c3c" if category == "LOKAL" else "#2980b9"
                
                daftar_artikel_html += f'''
                <div class="news-card" data-title="{title.lower()}">
                    <img src="{thumbnail}" alt="Thumbnail Berita" class="news-thumb" loading="lazy" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800&auto=format&fit=crop';">
                    <div class="news-info">
                        <span style="background:{cat_color};color:white;padding:3px 8px;border-radius:10px;font-size:0.75em;font-weight:bold;display:inline-block;margin-bottom:8px;">{category}</span>
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
        
        <!-- RUANG IKLAN POP-UNDER ADSTERRA (HEADER) -->
        <!-- Paste script pop-under Anda di sini -->
        <script src="https://pl31570858.profitableratecpmnetwork.com/bf/7c/c8/bf7cc8b38eeb859ad03672bf296c81ba.js"></script>
        
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; color: #333; }}
            
            header {{ background: #1a5276; color: white; padding: 30px 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .logo-container {{ display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 10px; }}
            .header-logo {{ width: 55px; height: 55px; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3)); }}
            header h1 {{ margin: 0; font-size: 2.5em; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }}
            
            .ad-slot {{ background: #fff; border: 1px dashed #ccc; padding: 15px; text-align: center; margin: 20px auto; max-width: 1100px; color: #888; font-weight: bold; }}
            .main-container {{ display: flex; flex-wrap: wrap; max-width: 1200px; margin: 0 auto; padding: 20px; gap: 30px; }}
            .content-left {{ flex: 1; min-width: 60%; }}
            
            /* CSS PENCARIAN */
            .search-box {{ width: 100%; padding: 12px 20px; margin-bottom: 20px; border: 2px solid #bdc3c7; border-radius: 25px; font-size: 1.1em; outline: none; transition: 0.3s; }}
            .search-box:focus {{ border-color: #1a5276; box-shadow: 0 0 8px rgba(26,82,118,0.2); }}
            
            .news-card {{ display: flex; background: #fff; border-radius: 8px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .news-thumb {{ width: 250px; height: 180px; object-fit: cover; flex-shrink: 0; background-color: #eaeaea; }}
            .news-info {{ padding: 20px; display: flex; flex-direction: column; justify-content: center; }}
            .news-info h3 {{ margin: 0 0 10px 0; font-size: 1.3em; line-height: 1.4; }}
            .news-info a {{ text-decoration: none; color: #333; }}
            .news-info a:hover {{ color: #1a5276; }}
            .news-info p {{ margin: 0; color: #666; font-size: 0.95em; line-height: 1.6; }}
            
            .pagination {{ display: flex; justify-content: center; align-items: center; margin: 30px 0; gap: 15px; }}
            .pagination button {{ padding: 10px 20px; background: #1a5276; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
            .pagination button:disabled {{ background: #ccc; cursor: not-allowed; }}
            
            .sidebar-right {{ width: 350px; flex-shrink: 0; }}
            
            /* CSS BANNER TELEGRAM STREAMING */
            .telegram-banner {{ background: linear-gradient(135deg, #0088cc, #00aaff); border-radius: 8px; padding: 20px; text-align: center; color: white; margin-bottom: 30px; box-shadow: 0 4px 10px rgba(0,136,204,0.3); }}
            .telegram-banner h3 {{ margin: 0 0 10px 0; font-size: 1.4em; }}
            .telegram-banner p {{ font-size: 0.95em; margin-bottom: 15px; opacity: 0.9; }}
            .btn-telegram {{ display: inline-block; background: #fff; color: #0088cc; padding: 10px 20px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 1.1em; transition: 0.3s; }}
            .btn-telegram:hover {{ transform: scale(1.05); box-shadow: 0 4px 10px rgba(255,255,255,0.4); }}
            
            .widget-box {{ background: #fff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 30px; overflow: hidden; border: 1px solid #eaeaea; }}
            .widget-box h3 {{ margin: 0; color: #fff; background: #1a5276; padding: 15px; text-align: center; font-size: 1.2em; }}
            
            .tab {{ display: flex; flex-wrap: wrap; background-color: #f1f1f1; border-bottom: 2px solid #1a5276; }}
            .tab button {{ background-color: inherit; color: #555; border: none; outline: none; cursor: pointer; padding: 12px 10px; font-size: 13px; font-weight: bold; flex-grow: 1; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; }}
            .tab button.active {{ background-color: #1a5276; color: white; border-bottom: none; }}
            .dynamic-widget-container {{ padding: 10px; min-height: 500px; text-align: center; }}
            
            @media (max-width: 900px) {{
                .main-container {{ flex-direction: column; }}
                .sidebar-right {{ width: 100%; }}
                .news-card {{ flex-direction: column; }}
                .news-thumb {{ width: 100%; height: 200px; }}
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

        <div class="ad-slot">Space Iklan Adsterra 728x90</div>

        <div class="main-container">
            <div class="content-left">
                <!-- FITUR PENCARIAN -->
                <input type="text" id="searchInput" class="search-box" placeholder="🔍 Cari berita bola di sini..." onkeyup="searchNews()">
                
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
                
                <!-- BANNER TELEGRAM STREAMING BOLA -->
                <div class="telegram-banner">
                    <h3>🔥 Nonton Bola Gratis!</h3>
                    <p>Gabung komunitas kami dan dapatkan link live streaming pertandingan bola terupdate setiap harinya tanpa bayar.</p>
                    <!-- Ganti tanda # dengan link grup telegram Anda -->
                    <a href="#" class="btn-telegram" rel="nofollow noopener noreferrer">Tonton Sekarang ➔</a>
                </div>

                <div class="widget-box">
                    <h3>🏆 KLASEMEN LIGA</h3>
                    <div class="tab">
                      <button class="tablinks active" onclick="loadWidget('ENG')">Inggris</button>
                      <button class="tablinks" onclick="loadWidget('ESP')">Spanyol</button>
                      <button class="tablinks" onclick="loadWidget('ITA')">Italia</button>
                      <button class="tablinks" onclick="loadWidget('GER')">Jerman</button>
                      <button class="tablinks" onclick="loadWidget('FRA')">Prancis</button>
                      <button class="tablinks" onclick="loadWidget('IDN')">Indonesia</button>
                    </div>
                    
                    <!-- SCRIPT INJECTION CONTAINER (ANTI BLANK) -->
                    <div id="dynamic-widget-container" class="dynamic-widget-container">
                        Mempersiapkan klasemen...
                    </div>
                </div>

                <div class="ad-slot">Space Iklan Adsterra 300x250</div>
            </div>
        </div>

        <!-- RUANG TRACKER HISTATS (HIDDEN) -->
        <div style="display:none;">
            <!-- Paste script Histats Anda di sini -->
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
        </div>

        <script>
            // FITUR PENCARIAN CLIENT-SIDE
            function searchNews() {{
                const input = document.getElementById('searchInput').value.toLowerCase();
                const cards = document.querySelectorAll('.news-card');
                let hasResults = false;
                
                // Jika sedang mencari, matikan paginasi
                if(input.length > 0) {{
                    document.querySelector('.pagination').style.display = 'none';
                    cards.forEach(card => {{
                        if (card.getAttribute('data-title').includes(input)) {{
                            card.style.display = 'flex';
                            hasResults = true;
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }});
                }} else {{
                    document.querySelector('.pagination').style.display = 'flex';
                    showPage(currentPage); // Kembalikan ke paginasi normal
                }}
            }}

            // FITUR DYNAMIC WIDGET INJECTION (MEMAKSA SCRIPT BERJALAN SAAT TAB DIKLIK)
            const scoreAxisWidgets = {{
                'ENG': {{ id: 'widget-atvlmumh1msi', url: 'https://widgets.scoreaxis.com/api/football/league-table/6232265abf1fa71a672159ec?widgetId=atvlmumh1msi&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }},
                'ESP': {{ id: 'widget-j7xwmumh3y7m', url: 'https://widgets.scoreaxis.com/api/football/league-table/62322c053617da0b83221cc6?widgetId=j7xwmumh3y7m&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }},
                'ITA': {{ id: 'widget-llkdmumh65vu', url: 'https://widgets.scoreaxis.com/api/football/league-table/62322b827aee66235a2be718?widgetId=llkdmumh65vu&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }},
                'GER': {{ id: 'widget-t6xvmumh55i6', url: 'https://widgets.scoreaxis.com/api/football/league-table/62321f50f7016c22d3650732?widgetId=t6xvmumh55i6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }},
                'FRA': {{ id: 'widget-bjs9mumh5ta6', url: 'https://widgets.scoreaxis.com/api/football/league-table/62322b4efd209951602c9096?widgetId=bjs9mumh5ta6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }},
                'IDN': {{ id: 'widget-wrt7mumh7146', url: 'https://widgets.scoreaxis.com/api/football/league-table/623225c009ac1611ee0dc0f6?widgetId=wrt7mumh7146&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }}
            }};

            function loadWidget(leagueKey) {{
                // Update styling tombol aktif
                let tablinks = document.getElementsByClassName("tablinks");
                for (let i = 0; i < tablinks.length; i++) {{ tablinks[i].classList.remove("active"); }}
                event.currentTarget.classList.add("active");

                // Eksekusi ulang Script Widget agar render sempurna
                const container = document.getElementById("dynamic-widget-container");
                const wData = scoreAxisWidgets[leagueKey];
                
                // Buat kerangka div baru
                container.innerHTML = `<div id="${{wData.id}}" class="scoreaxis-widget" style="width: 100%;"><p style="padding:20px;color:#888;">Memuat Data...</p></div>`;
                
                // Suntikkan script
                const scriptEl = document.createElement('script');
                scriptEl.src = wData.url;
                scriptEl.async = true;
                document.getElementById(wData.id).appendChild(scriptEl);
            }}

            // FITUR PAGINASI
            const itemsPerPage = 6;
            let currentPage = 1;
            const articles = document.querySelectorAll('.news-card');
            const totalPages = Math.ceil(articles.length / itemsPerPage);

            function showPage(page) {{
                // Pastikan fungsi ini tidak berjalan saat fitur Search aktif
                if(document.getElementById('searchInput').value.length > 0) return;
                
                articles.forEach((card, index) => {{
                    if (index >= (page - 1) * itemsPerPage && index < page * itemsPerPage) {{
                        card.style.display = 'flex';
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                if(document.getElementById('page-info')) document.getElementById('page-info').innerText = `Halaman ${{page}} dari ${{totalPages}}`;
                if(document.getElementById('btn-prev')) document.getElementById('btn-prev').disabled = page === 1;
                if(document.getElementById('btn-next')) document.getElementById('btn-next').disabled = page === totalPages || totalPages === 0;
            }}

            function changePage(delta) {{
                currentPage += delta;
                showPage(currentPage);
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}

            // Inisialisasi awal
            if(articles.length > 0) showPage(1);
            // Panggil widget Inggris pertama kali
            window.onload = function() {{ loadWidget('ENG'); }};
        </script>
    </body>
    </html>
    """
    
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage_template)

def main():
    try:
        all_news_items = []
        for source in RSS_SOURCES:
            try:
                response = requests.get(f"https://api.rss2json.com/v1/api.json?rss_url={source}", timeout=10)
                data = response.json()
                if 'items' in data:
                    all_news_items.extend(data['items'])
            except Exception:
                pass
                
        if not all_news_items:
            return
            
        random.shuffle(all_news_items)
            
        for item in all_news_items[:5]: 
            content, title, excerpt, thumb, category = generate_article_with_gemini(item)
            if content:
                save_as_html(content, title, excerpt, thumb, category)
        
        update_homepage()
                
    except Exception as e:
        print(f"ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
