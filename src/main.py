# Ini adalah file utama untuk script scraper Python

import os
import random
import time
import requests
from google import genai
import json
import re

print("=== MEMULAI SCRIPT AGC BOLA (MULTI-SUMBER) ===")

API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    print("ERROR: GEMINI_API_KEYS tidak ditemukan!")
    raise ValueError("GEMINI_API_KEYS belum di-set di GitHub.")

API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]

# ==========================================
# DAFTAR KANAL BERITA (DALAM & LUAR NEGERI)
# ==========================================
RSS_SOURCES = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml", # Luar Negeri (BBC Football)
    "https://www.espn.com/espn/rss/soccer/news",       # Luar Negeri (ESPN Soccer)
    "https://www.bola.net/feed/",                      # Dalam Negeri (Bola.net)
    "https://www.suara.com/rss/bola"                   # Dalam Negeri (Suara Bola)
]

OUTPUT_DIR = "public/berita"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_gemini_response(prompt):
    random.shuffle(API_KEYS_LIST)
    
    ai_models = [
        'gemini-3.8-flash', 
        'gemini-3.7-flash', 
        'gemini-2.5-flash', 
        'gemini-2.0-flash', 
        'gemini-1.5-flash'
    ]
    
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
    
    # Prompt diubah agar AI siap menerima teks sumber berbahasa Inggris maupun Indonesia
    prompt = f"""
    Bertindaklah sebagai jurnalis sepak bola profesional dari Indonesia. 
    Saya memiliki sumber berita sepak bola berikut (bisa berbahasa Inggris atau Indonesia):
    
    - Judul Asli: {title}
    - Ringkasan: {description}
    
    Tugas Anda:
    Tulis ulang berita ini menjadi artikel berita sepak bola berbahasa Indonesia yang orisinal, tajam, dan informatif (sekitar 300 kata). 
    Hindari plagiarisme dari teks asli.
    
    Wajib gunakan struktur Markdown berikut:
    # [Tulis Judul Artikel Baru dalam Bahasa Indonesia yang Clickbait, SEO-Friendly & Menarik]
    
    [Paragraf Pembuka yang merangkum inti berita secara dramatis]
    
    ## [Sub-heading 1 Bahasa Indonesia]
    [Isi paragraf ulasan/analisis]
    
    ## [Sub-heading 2 Bahasa Indonesia]
    [Isi paragraf ulasan/analisis]
    
    PENTING: Jangan tambahkan kata pengantar atau penutup dari AI.
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        indo_title = title 
        for line in article_content.split('\n'):
            if line.startswith('# '):
                indo_title = line.replace('# ', '').strip()
                # Bersihkan jika ada tanda bintang bold bawaan markdown di judul
                indo_title = indo_title.replace('**', '')
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

def main():
    try:
        all_news_items = []
        
        print("\nMengumpulkan berita dari berbagai sumber...")
        for source in RSS_SOURCES:
            api_url = f"https://api.rss2json.com/v1/api.json?rss_url={source}"
            try:
                response = requests.get(api_url, timeout=10)
                data = response.json()
                if 'items' in data:
                    all_news_items.extend(data['items'])
                    print(f"- Sukses mengambil dari: {source}")
            except Exception as e:
                print(f"- Gagal mengambil dari {source}: {e}")
                
        if not all_news_items:
            print("PERHATIAN: Tidak ada data berita sama sekali. Proses dihentikan.")
            return
            
        print(f"\nTotal keseluruhan berita terkumpul: {len(all_news_items)}")
        
        # Mengacak urutan berita agar hasil generate selalu bervariasi (mix lokal & internasional)
        random.shuffle(all_news_items)
            
        # Ambil 5 berita acak teratas untuk di-rewrite
        for item in all_news_items[:5]: 
            content, indo_title = generate_article_with_gemini(item)
            if content:
                save_as_html(content, indo_title)
                
    except Exception as e:
        print(f"ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
