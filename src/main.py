# Ini adalah file utama untuk script scraper Python

import os
import random
import time
import requests
from google import genai
import json
import re
from datetime import datetime

print("=== MEMULAI SCRIPT AGC BOLA PRO (SEO + KLASEMEN) ===")

API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    print("ERROR: GEMINI_API_KEYS tidak ditemukan!")
    raise ValueError("GEMINI_API_KEYS belum di-set di GitHub.")

API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]

# Sumber RSS Berita
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
                    # Membersihkan backticks jika Gemini memaksa mereturn blok kode
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
    
    # Mengekstrak Gambar Thumbnail dari RSS
    thumbnail = news_item.get('thumbnail', '')
    if not thumbnail and 'enclosure' in news_item and isinstance(news_item['enclosure'], dict):
        thumbnail = news_item['enclosure'].get('link', '')
    if not thumbnail:
        # Gambar cadangan jika sumber RSS pelit gambar
        thumbnail = "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800&auto=format&fit=crop"
        
    print(f"\n======================================")
    print(f"Mengolah Info Asli: {title}")
    
    prompt = f"""
    Bertindaklah sebagai jurnalis sepak bola profesional dari Indonesia. 
    Sumber berita:
    - Judul Asli: {title}
    - Ringkasan: {description}
    
    Tulis ulang berita ini menjadi artikel berita sepak bola berbahasa Indonesia yang SEO-friendly (minimal 300 kata). 
    
    ATURAN FORMATTING (SANGAT PENTING):
    1. WAJIB gunakan HTML murni. JANGAN gunakan markdown (seperti tanda # atau **).
    2. Baris paling pertama WAJIB berupa tag <h1> berisi Judul Baru yang clickbait.
    3. Paragraf pembuka wajib menggunakan tag <p>.
    4. Gunakan tag <h2> untuk sub-judul di tengah artikel.
    5. Jangan tambahkan tulisan pengantar/penutup apapun. Langsung hasilkan HTML.
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        # Ekstrak Judul dari <h1>
        indo_title = title 
        title_match = re.search(r'<h1>(.*?)</h1>', article_content, re.IGNORECASE)
        if title_match:
            indo_title = title_match.group(1).strip()
            # Hapus <h1> dari body karena kita akan meletakkannya manual di template
            article_content = re.sub(r'<h1>.*?</h1>', '', article_content, count=1, flags=re.IGNORECASE)
            
        # Ekstrak ringkasan (150 huruf paragraf pertama) untuk Meta SEO
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
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <!-- SEO META TAGS -->
        <title>{title} - Lensa Terkini Bola</title>
        <meta name="description" content="{excerpt}">
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="{excerpt}">
        <meta property="og:image" content="{thumbnail}">
        <meta property="og:type" content="article">
        
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; background: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            header {{ border-bottom: 2px solid #1a5276; margin-bottom: 20px; padding-bottom: 10px; }}
            h1 {{ color: #1a5276; font-size: 2.2em; line-height: 1.3; margin-top: 0; }}
            h2 {{ color: #2980b9; margin-top: 30px; }}
            .hero-img {{ width: 100%; max-height: 450px; object-fit: cover; border-radius: 8px; margin-bottom: 20px; }}
            .ad-slot {{ background: #eaeaea; border: 1px dashed #bbb; padding: 15px; text-align: center; margin: 20px 0; color: #777; font-weight: bold; font-size: 0.9em; }}
            p {{ line-height: 1.7; font-size: 1.05em; }}
            .back-btn {{ display: inline-block; padding: 12px 20px; background: #1a5276; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; font-weight: bold; transition: background 0.3s; }}
            .back-btn:hover {{ background: #154360; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <a href="/" style="text-decoration: none; color: #7f8c8d; font-weight: bold;">&larr; Lensa Terkini Bola</a>
            </header>
            
            <h1>{title}</h1>
            <img src="{thumbnail}" alt="{title}" class="hero-img">
            
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
    berita_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.html')]
    berita_files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
    
    daftar_artikel_html = ""
    for filename in berita_files:
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
                # Ekstrak Meta Data untuk Kartu Homepage
                title = re.search(r'<title>(.*?)</title>', html_content).group(1).replace(' - Lensa Terkini Bola', '')
                
                excerpt_match = re.search(r'<meta name="description" content="(.*?)">', html_content)
                excerpt = excerpt_match.group(1) if excerpt_match else "Baca berita selengkapnya..."
                
                img_match = re.search(r'<meta property="og:image" content="(.*?)">', html_content)
                thumbnail = img_match.group(1) if img_match else "https://via.placeholder.com/150"
                
                # Desain Kartu Artikel (Kiri Gambar, Kanan Teks)
                daftar_artikel_html += f'''
                <div class="news-card">
                    <img src="{thumbnail}" alt="{title}" class="news-thumb">
                    <div class="news-info">
                        <h3><a href="/berita/{filename}">{title}</a></h3>
                        <p>{excerpt}</p>
                    </div>
                </div>\n'''
        except Exception:
            continue

    # Template Halaman Utama (Homepage) dengan Grid & Paginasi
    homepage_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lensa Terkini Bola - Klasemen & Berita Terupdate</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; color: #333; }}
            header {{ background: #1a5276; color: white; padding: 30px 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            header h1 {{ margin: 0; font-size: 2.5em; }}
            header p {{ margin: 10px 0 0 0; opacity: 0.8; font-size: 1.1em; }}
            
            .ad-slot {{ background: #fff; border: 1px dashed #ccc; padding: 15px; text-align: center; margin: 20px auto; max-width: 1100px; color: #888; font-weight: bold; }}
            
            .main-container {{ display: flex; flex-wrap: wrap; max-width: 1200px; margin: 0 auto; padding: 20px; gap: 30px; }}
            
            /* Bagian Kiri (Berita) */
            .content-left {{ flex: 1; min-width: 60%; }}
            .section-title {{ border-left: 5px solid #1a5276; padding-left: 15px; color: #1a5276; font-size: 1.8em; margin-bottom: 25px; }}
            
            .news-card {{ display: flex; background: #fff; border-radius: 8px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: transform 0.2s; }}
            .news-card:hover {{ transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .news-thumb {{ width: 250px; height: 180px; object-fit: cover; flex-shrink: 0; }}
            .news-info {{ padding: 20px; }}
            .news-info h3 {{ margin: 0 0 10px 0; font-size: 1.3em; line-height: 1.4; }}
            .news-info a {{ text-decoration: none; color: #333; }}
            .news-info a:hover {{ color: #1a5276; }}
            .news-info p {{ margin: 0; color: #666; font-size: 0.95em; line-height: 1.6; }}
            
            /* Paginasi */
            .pagination {{ display: flex; justify-content: center; align-items: center; margin: 30px 0; gap: 15px; }}
            .pagination button {{ padding: 10px 20px; background: #1a5276; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
            .pagination button:disabled {{ background: #ccc; cursor: not-allowed; }}
            .pagination span {{ font-weight: bold; }}

            /* Bagian Kanan (Klasemen Sidebar) */
            .sidebar-right {{ width: 320px; flex-shrink: 0; }}
            .widget-box {{ background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 30px; }}
            .widget-box h3 {{ margin-top: 0; color: #2980b9; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; text-align: center; }}
            
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
            <!-- KOLOM KIRI: BERITA TERBARU -->
            <div class="content-left">
                <h2 class="section-title">Berita Utama</h2>
                <div id="news-list">
                    {daftar_artikel_html}
                </div>
                
                <!-- KONTROL PAGINASI -->
                <div class="pagination">
                    <button id="btn-prev" onclick="changePage(-1)">&#8592; Sebelumnya</button>
                    <span id="page-info">Halaman 1</span>
                    <button id="btn-next" onclick="changePage(1)">Selanjutnya &#8594;</button>
                </div>
            </div>

            <!-- KOLOM KANAN: KLASEMEN (IFRAME WIDGET) -->
            <div class="sidebar-right">
                <div class="widget-box">
                    <h3>Klasemen Liga Inggris</h3>
                    <!-- Widget Gratis dari FCTables -->
                    <iframe frameborder="0" scrolling="yes" width="100%" height="450" src="https://www.fctables.com/england/premier-league/iframe/?type=table&lang=id&country=67&template=10&team=&timezone=Asia/Jakarta&time=24&width=100%&height=450&font=Arial&fs=12&lh=22&bg=FFFFFF&fc=333333&logo=1&tlink=1&ths=1&thb=1&thba=FFFFFF&thc=000000&bc=dddddd&tc=333333&hp=1&bch=1&ff=1&wm=1"></iframe>
                </div>
                
                <div class="ad-slot">Iklan 300x250</div>
                
                <div class="widget-box">
                    <h3>Klasemen Liga 1 Indonesia</h3>
                    <!-- Widget Gratis dari FCTables -->
                    <iframe frameborder="0" scrolling="yes" width="100%" height="450" src="https://www.fctables.com/indonesia/super-liga/iframe/?type=table&lang=id&country=105&template=10&team=&timezone=Asia/Jakarta&time=24&width=100%&height=450&font=Arial&fs=12&lh=22&bg=FFFFFF&fc=333333&logo=1&tlink=1&ths=1&thb=1&thba=FFFFFF&thc=000000&bc=dddddd&tc=333333&hp=1&bch=1&ff=1&wm=1"></iframe>
                </div>
            </div>
        </div>

        <!-- SCRIPT UNTUK FUNGSI PAGINASI -->
        <script>
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
                document.getElementById('btn-prev').disabled = page === 1;
                document.getElementById('btn-next').disabled = page === totalPages || totalPages === 0;
            }}

            function changePage(delta) {{
                currentPage += delta;
                showPage(currentPage);
                // Auto scroll ke atas saat ganti halaman
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}

            // Inisialisasi Paginasi saat halaman dimuat
            if(articles.length > 0) showPage(1);
        </script>
    </body>
    </html>
    """
    
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage_template)
    print("V Homepage (index.html) berhasil diperbarui!")

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
