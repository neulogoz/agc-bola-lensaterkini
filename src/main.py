# Ini adalah file utama untuk script scraper Python

import os
import random
import time
import requests
from google import genai
import json
import re
from datetime import datetime

print("=== MEMULAI SCRIPT AGC BOLA ===")

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
                    return response.text
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
    
    print(f"\n======================================")
    print(f"Mengolah Info Asli: {title}")
    
    prompt = f"""
    Bertindaklah sebagai jurnalis sepak bola profesional dari Indonesia. 
    Saya memiliki sumber berita sepak bola berikut:
    
    - Judul Asli: {title}
    - Ringkasan: {description}
    
    Tulis ulang berita ini menjadi artikel berita sepak bola berbahasa Indonesia yang orisinal, tajam, dan informatif (sekitar 300 kata). 
    
    Wajib gunakan struktur Markdown berikut:
    # [Tulis Judul Artikel Baru dalam Bahasa Indonesia yang Clickbait, SEO-Friendly & Menarik]
    
    [Paragraf Pembuka]
    
    ## [Sub-heading 1 Bahasa Indonesia]
    [Isi paragraf]
    
    ## [Sub-heading 2 Bahasa Indonesia]
    [Isi paragraf]
    
    PENTING: Jangan tambahkan kata pengantar atau penutup dari AI.
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        indo_title = title 
        for line in article_content.split('\n'):
            if line.startswith('# '):
                indo_title = line.replace('# ', '').strip().replace('**', '')
                break
        print(f"-> Judul AI: {indo_title}")
        return article_content, indo_title
    return None, None

def save_as_html(markdown_content, indo_title):
    slug = re.sub(r'[^a-zA-Z0-9]', '-', indo_title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    filename = f"{OUTPUT_DIR}/{slug}.html"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{indo_title} - Lensa Terkini Bola</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
            h1, h2 {{ color: #1a5276; line-height: 1.3; }}
            .ad-slot {{ background: #f4f4f4; border: 1px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; color: #888; font-weight: bold; }}
            .back-btn {{ display: inline-block; padding: 10px 15px; background: #1a5276; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="ad-slot">Space Iklan Adsterra 728x90</div>
        <article>{markdown_content}</article>
        <div class="ad-slot">Space Iklan Adsterra 300x250</div>
        <a href="/" class="back-btn">Kembali ke Beranda</a>
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"V Tersimpan sebagai: {filename}")

def update_homepage():
    """Membaca semua file di folder berita dan membuat index.html"""
    print("\nMemperbarui Halaman Utama (Homepage)...")
    
    # Ambil semua file HTML di folder berita
    berita_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.html')]
    
    # Urutkan berdasarkan waktu modifikasi terbaru (Artikel terbaru di atas)
    berita_files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
    
    daftar_artikel_html = ""
    for filename in berita_files:
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Ekstrak judul dari tag <title>
                title_match = re.search(r'<title>(.*?)</title>', content)
                if title_match:
                    clean_title = title_match.group(1).replace(' - Lensa Terkini Bola', '')
                else:
                    clean_title = filename.replace('.html', '').replace('-', ' ').title()
                
                # Format list artikel
                daftar_artikel_html += f'''
                <div class="news-card">
                    <a href="/berita/{filename}">{clean_title}</a>
                </div>\n'''
        except Exception as e:
            print(f"Gagal membaca {filename}: {e}")

    # Template Homepage
    homepage_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lensa Terkini Bola - Portal Berita Sepak Bola</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; background-color: #f9f9f9; }}
            header {{ text-align: center; padding: 30px 0; border-bottom: 3px solid #1a5276; margin-bottom: 30px; }}
            h1 {{ color: #1a5276; margin: 0; font-size: 2.5em; }}
            .ad-slot {{ background: #fff; border: 1px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; color: #888; font-weight: bold; }}
            .news-container {{ display: flex; flex-direction: column; gap: 15px; }}
            .news-card {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #1a5276; transition: transform 0.2s; }}
            .news-card:hover {{ transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .news-card a {{ text-decoration: none; color: #333; font-size: 1.2em; font-weight: bold; }}
            .news-card a:hover {{ color: #1a5276; }}
            footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
        </style>
    </head>
    <body>
        <header>
            <h1>Lensa Terkini Bola</h1>
            <p>Update Berita Sepak Bola Lokal & Internasional</p>
        </header>

        <div class="ad-slot">Space Iklan Adsterra 728x90</div>

        <h2>Berita Terbaru</h2>
        <div class="news-container">
            {daftar_artikel_html}
        </div>

        <div class="ad-slot">Space Iklan Adsterra 300x250</div>

        <footer>
            &copy; {datetime.now().year} Lensa Terkini Bola. Ter-update otomatis.
        </footer>
    </body>
    </html>
    """
    
    # Simpan sebagai index.html di root public/
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
            content, indo_title = generate_article_with_gemini(item)
            if content:
                save_as_html(content, indo_title)
        
        # Panggil fungsi pembuat homepage setelah semua artikel selesai digenerate
        update_homepage()
                
    except Exception as e:
        print(f"ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
