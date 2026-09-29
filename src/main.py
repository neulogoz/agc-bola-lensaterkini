import os
import random
import time
import requests
from google import genai
import json
import re
from datetime import datetime

print("=== MEMULAI SCRIPT AGC BOLA (DESAIN TAB KLASEMEN MEWAH) ===")

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
        
    print(f"\n======================================")
    print(f"Mengolah Info Asli: {title}")
    
    prompt = f"""
    Bertindaklah sebagai jurnalis sepak bola profesional dari Indonesia. 
    Tulis ulang berita berikut menjadi artikel berita sepak bola berbahasa Indonesia (minimal 300 kata).
    
    Data Asli:
    - Judul: {title}
    - Ringkasan: {description}
    
    ATURAN FORMATTING (SANGAT PENTING - DILARANG MELANGGAR):
    1. WAJIB keluarkan dalam format HTML MURNI.
    2. DILARANG KERAS menggunakan format Markdown (JANGAN ADA tanda # atau ** sama sekali).
    3. Baris pertama wajib: <h1>[Judul Clickbait Bahasa Indonesia]</h1>
    4. Sub-judul gunakan: <h2>[Sub-judul]</h2>
    5. Setiap paragraf biasa WAJIB dibungkus tag <p> dan </p>.
    6. Jangan buat kata pengantar. Langsung mulai dari tag <h1>.
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        article_content = article_content.replace('**', '') 
        article_content = re.sub(r'^#+\s*', '', article_content, flags=re.MULTILINE) 
        
        indo_title = title 
        title_match = re.search(r'<h1>(.*?)</h1>', article_content, re.IGNORECASE)
        if title_match:
            indo_title = title_match.group(1).strip()
            article_content = re.sub(r'<h1>.*?</h1>', '', article_content, count=1, flags=re.IGNORECASE)
            
        lines = article_content.split('\n')
        clean_html = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not line.startswith('<'):
                line = f"<p>{line}</p>"
            clean_html.append(line)
            
        article_content = '\n'.join(clean_html)
        
        excerpt = "Berita sepak bola terbaru dan terhangat dari dalam dan luar negeri."
        p_match = re.search(r'<p>(.*?)</p>', article_content, re.IGNORECASE)
        if p_match:
            excerpt = re.sub(r'<[^>]+>', '', p_match.group(1))[:150] + "..."
            
        print(f"-> Judul AI: {indo_title}")
        return article_content, indo_title, excerpt, thumbnail
    return None, None, None, None

def save_as_html(content, title, excerpt, thumbnail):
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
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; background: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            header {{ border-bottom: 2px solid #1a5276; margin-bottom: 20px; padding-bottom: 10px; }}
            h1 {{ color: #1a5276; font-size: 2.2em; line-height: 1.3; margin-top: 0; }}
            h2 {{ color: #2980b9; margin-top: 30px; font-size: 1.5em; }}
            .hero-img {{ width: 100%; max-height: 450px; object-fit: cover; border-radius: 8px; margin-bottom: 20px; background-color: #eaeaea; }}
            .ad-slot {{ background: #eaeaea; border: 1px dashed #bbb; padding: 15px; text-align: center; margin: 20px 0; color: #777; font-weight: bold; font-size: 0.9em; }}
            p {{ line-height: 1.8; font-size: 1.1em; margin-bottom: 15px; text-align: justify; }}
            .back-btn {{ display: inline-block; padding: 12px 20px; background: #1a5276; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; font-weight: bold; }}
            .back-btn:hover {{ background: #154360; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <a href="/" style="text-decoration: none; color: #7f8c8d; font-weight: bold;">&larr; Lensa Terkini Bola</a>
            </header>
            
            <h1>{title}</h1>
            <img src="{thumbnail}" alt="{title}" class="hero-img" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1518605368461-1e1c071d3326?q=80&w=800&auto=format&fit=crop';">
            
            <div class="ad-slot">Space Iklan Adsterra 728x90</div>
            
            <article>{content}</article>
            
            <div class="ad-slot">Space Iklan Adsterra 300x250</div>
            <a href="/" class="back-btn">Kembali ke Beranda</a>
        </div>
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"V Tersimpan sebagai: {filename}")

def update_homepage():
    print("\nMemperbarui Halaman Utama (Homepage)...")
    
    def get_file_timestamp(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'<meta name="publish-date" content="(\d+)">', content)
                if match:
                    return int(match.group(1))
        except:
            pass
        return 0 
        
    berita_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.html')]
    berita_files.sort(key=lambda x: get_file_timestamp(os.path.join(OUTPUT_DIR, x)), reverse=True)
    
    daftar_artikel_html = ""
    for filename in berita_files:
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
                title_match = re.search(r'<title>(.*?)</title>', html_content)
                title = title_match.group(1).replace(' - Lensa Terkini Bola', '') if title_match else filename
                
                excerpt_match = re.search(r'<meta name="description" content="(.*?)">', html_content)
                excerpt = excerpt_match.group(1) if excerpt_match else "Baca selengkapnya..."
                
                img_match = re.search(r'<img src="(.*?)" alt=".*?" class="hero-img"', html_content)
                thumbnail = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1518605368461-1e1c071d3326?q=80&w=800&auto=format&fit=crop"
                
                daftar_artikel_html += f'''
                <div class="news-card">
                    <img src="{thumbnail}" alt="Thumbnail Berita" class="news-thumb" loading="lazy" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800&auto=format&fit=crop';">
                    <div class="news-info">
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
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; color: #333; }}
            header {{ background: #1a5276; color: white; padding: 30px 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            header h1 {{ margin: 0; font-size: 2.5em; }}
            header p {{ margin: 10px 0 0 0; opacity: 0.8; font-size: 1.1em; }}
            
            .ad-slot {{ background: #fff; border: 1px dashed #ccc; padding: 15px; text-align: center; margin: 20px auto; max-width: 1100px; color: #888; font-weight: bold; }}
            
            .main-container {{ display: flex; flex-wrap: wrap; max-width: 1200px; margin: 0 auto; padding: 20px; gap: 30px; }}
            
            .content-left {{ flex: 1; min-width: 60%; }}
            .section-title {{ border-left: 5px solid #1a5276; padding-left: 15px; color: #1a5276; font-size: 1.8em; margin-bottom: 25px; }}
            
            .news-card {{ display: flex; background: #fff; border-radius: 8px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .news-thumb {{ width: 250px; height: 180px; object-fit: cover; flex-shrink: 0; background-color: #eaeaea; }}
            .news-info {{ padding: 20px; display: flex; flex-direction: column; justify-content: center; }}
            .news-info h3 {{ margin: 0 0 10px 0; font-size: 1.3em; line-height: 1.4; }}
            .news-info a {{ text-decoration: none; color: #333; transition: color 0.2s; }}
            .news-info a:hover {{ color: #1a5276; }}
            .news-info p {{ margin: 0; color: #666; font-size: 0.95em; line-height: 1.6; }}
            
            .pagination {{ display: flex; justify-content: center; align-items: center; margin: 30px 0; gap: 15px; }}
            .pagination button {{ padding: 10px 20px; background: #1a5276; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
            .pagination button:disabled {{ background: #ccc; cursor: not-allowed; }}
            .pagination span {{ font-weight: bold; }}

            .sidebar-right {{ width: 350px; flex-shrink: 0; }}
            
            /* CSS KHUSUS DESAIN MENU TAB */
            .widget-box {{ background: #fff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 30px; overflow: hidden; border: 1px solid #eaeaea; }}
            .widget-box h3 {{ margin: 0; color: #fff; background: #1a5276; padding: 15px; text-align: center; font-size: 1.2em; letter-spacing: 1px; }}
            
            .tab {{ display: flex; flex-wrap: wrap; background-color: #f1f1f1; border-bottom: 2px solid #1a5276; }}
            .tab button {{ background-color: inherit; color: #555; border: none; outline: none; cursor: pointer; padding: 12px 10px; transition: 0.3s; font-size: 13px; font-weight: bold; flex-grow: 1; text-align: center; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; }}
            .tab button:hover {{ background-color: #ddd; }}
            .tab button.active {{ background-color: #1a5276; color: white; border-bottom: none; }}
            
            .tabcontent {{ display: none; padding: 15px 10px; animation: fadeEffect 0.5s; }}
            @keyframes fadeEffect {{ from {{opacity: 0;}} to {{opacity: 1;}} }}
            
            .widget-content {{ max-height: 600px; overflow-y: auto; overflow-x: hidden; border-radius: 5px; }}
            
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
            <h1>Lensa Terkini Bola</h1>
            <p>Berita & Klasemen Sepak Bola Dalam & Luar Negeri</p>
        </header>

        <div class="ad-slot">Space Iklan Adsterra 728x90</div>

        <div class="main-container">
            <div class="content-left">
                <h2 class="section-title">Berita Terbaru</h2>
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
                
                <!-- WIDGET KLASEMEN DENGAN SISTEM TAB -->
                <div class="widget-box">
                    <h3>🏆 PUSAT KLASEMEN LIGA</h3>
                    
                    <!-- Menu Tombol Navigasi Liga -->
                    <div class="tab">
                      <button class="tablinks active" onclick="openLeague(event, 'ENG')">Inggris</button>
                      <button class="tablinks" onclick="openLeague(event, 'ESP')">Spanyol</button>
                      <button class="tablinks" onclick="openLeague(event, 'ITA')">Italia</button>
                      <button class="tablinks" onclick="openLeague(event, 'GER')">Jerman</button>
                      <button class="tablinks" onclick="openLeague(event, 'FRA')">Prancis</button>
                      <button class="tablinks" onclick="openLeague(event, 'IDN')">Indonesia</button>
                    </div>

                    <!-- Isi Tab Liga Inggris (Default Terbuka) -->
                    <div id="ENG" class="tabcontent" style="display: block;">
                        <div class="widget-content">
                            <div id="widget-atvlmumh1msi" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/6232265abf1fa71a672159ec?widgetId=atvlmumh1msi&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>
                        </div>
                    </div>

                    <!-- Isi Tab Liga Spanyol -->
                    <div id="ESP" class="tabcontent">
                        <div class="widget-content">
                            <div id="widget-j7xwmumh3y7m" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62322c053617da0b83221cc6?widgetId=j7xwmumh3y7m&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>
                        </div>
                    </div>

                    <!-- Isi Tab Liga Italia -->
                    <div id="ITA" class="tabcontent">
                        <div class="widget-content">
                            <div id="widget-llkdmumh65vu" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62322b827aee66235a2be718?widgetId=llkdmumh65vu&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>
                        </div>
                    </div>

                    <!-- Isi Tab Liga Jerman -->
                    <div id="GER" class="tabcontent">
                        <div class="widget-content">
                            <div id="widget-t6xvmumh55i6" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62321f50f7016c22d3650732?widgetId=t6xvmumh55i6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>
                        </div>
                    </div>

                    <!-- Isi Tab Liga Prancis -->
                    <div id="FRA" class="tabcontent">
                        <div class="widget-content">
                            <div id="widget-bjs9mumh5ta6" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/62322b4efd209951602c9096?widgetId=bjs9mumh5ta6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>
                        </div>
                    </div>

                    <!-- Isi Tab Liga Indonesia -->
                    <div id="IDN" class="tabcontent">
                        <div class="widget-content">
                            <div id="widget-wrt7mumh7146" class="scoreaxis-widget" style="width: auto;height: auto;font-size: 14px;background-color: #ffffff;color: #141416;border: 1px solid;border-color: #ecf1f7;overflow: auto;"><script src="https://widgets.scoreaxis.com/api/football/league-table/623225c009ac1611ee0dc0f6?widgetId=wrt7mumh7146&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=heebo&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd" async></script><div class="widget-main-link" style="padding: 6px 12px;font-weight: 500;">Live data by <a href="https://www.scoreaxis.com/" style="color: inherit;">Scoreaxis</a></div></div>
                        </div>
                    </div>
                </div>

                <div class="ad-slot">Space Iklan Adsterra 300x250</div>
                
            </div>
        </div>

        <script>
            // FUNGSI UNTUK MENU TAB KLASEMEN
            function openLeague(evt, leagueName) {{
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].style.display = "none";
                }}
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {{
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }}
                document.getElementById(leagueName).style.display = "block";
                evt.currentTarget.className += " active";
            }}

            // FUNGSI UNTUK PAGINASI ARTIKEL
            const itemsPerPage = 6;
            let currentPage = 1;
            const articles = document.querySelectorAll('.news-card');
            const totalPages = Math.ceil(articles.length / itemsPerPage);

            function showPage(page) {{
                articles.forEach((card, index) => {{
                    if (index >= (page - 1) * itemsPerPage && index < page * itemsPerPage) {{
                        card.style.display = 'flex';
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                document.getElementById('page-info').innerText = `Halaman ${{page}} dari ${{totalPages}}`;
                if(document.getElementById('btn-prev')) document.getElementById('btn-prev').disabled = page === 1;
                if(document.getElementById('btn-next')) document.getElementById('btn-next').disabled = page === totalPages || totalPages === 0;
            }}

            function changePage(delta) {{
                currentPage += delta;
                showPage(currentPage);
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}

            if(articles.length > 0) showPage(1);
        </script>
    </body>
    </html>
    """
    
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage_template)
    print("V Homepage (index.html) berhasil diperbarui dengan Menu Tab Mewah!")

def main():
    try:
        all_news_items = []
        print("\nMengumpulkan berita...")
        for source in RSS_SOURCES:
            api_url = f"https://api.rss2json.com/v1/api.json?rss_url={source}"
            try:
                response = requests.get(api_url, timeout=10)
                data = response.json()
                if 'items' in data:
                    all_news_items.extend(data['items'])
            except Exception:
                pass
                
        if not all_news_items:
            print("PERHATIAN: Tidak ada data berita sama sekali.")
            return
            
        random.shuffle(all_news_items)
            
        for item in all_news_items[:5]: 
            content, title, excerpt, thumbnail = generate_article_with_gemini(item)
            if content:
                save_as_html(content, title, excerpt, thumbnail)
        
        update_homepage()
                
    except Exception as e:
        print(f"ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
