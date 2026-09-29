# Ini adalah file utama untuk script scraper Python

import os
import random
import time
import requests
from google import genai
import json
import re

print("=== MEMULAI SCRIPT AGC BOLA (VIA RSS) ===")

API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    print("ERROR: GEMINI_API_KEYS tidak ditemukan!")
    raise ValueError("GEMINI_API_KEYS belum di-set di GitHub.")

API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]
RSS_URL = "https://api.rss2json.com/v1/api.json?rss_url=https://www.skysports.com/rss/12040"
OUTPUT_DIR = "public/berita"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"API Keys berhasil di-load: {len(API_KEYS_LIST)} kunci.")

def get_gemini_response(prompt):
    random.shuffle(API_KEYS_LIST)
    
    # Memasukkan Gemini 3.8 dan 3.7 di urutan prioritas teratas sesuai saran Anda
    ai_models = [
        'gemini-3.8-flash', 
        'gemini-3.7-flash', 
        'gemini-2.5-flash', 
        'gemini-2.0-flash', 
        'gemini-1.5-flash'
    ]
    
    for current_key in API_KEYS_LIST:
        try:
            print(f"\nMenggunakan API Key: {current_key[:10]}...")
            client = genai.Client(api_key=current_key)
            
            for model_name in ai_models:
                try:
                    print(f"-> Memanggil model: {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    print("=> SUKSES! Artikel berhasil ditulis oleh Gemini.")
                    return response.text
                except Exception as model_err:
                    err_msg = str(model_err)
                    if "404" in err_msg or "not found" in err_msg.lower():
                        print(f"   X Model {model_name} tidak tersedia, mencoba model berikutnya...")
                        continue 
                    else:
                        raise model_err 
                        
        except Exception as e:
            error_msg = str(e)
            print(f"-> API Key gagal. Error: {error_msg}")
            if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                time.sleep(2)
                continue
            else:
                continue
    
    print("FATAL: Semua API Key dan Model AI gagal digunakan.")
    return None

def generate_article_with_gemini(news_item):
    title = news_item.get('title', 'Berita Bola')
    description = news_item.get('description', '')
    pub_date = news_item.get('pubDate', '')
    
    print(f"\n======================================")
    print(f"Memproses Berita: {title}")
    
    prompt = f"""
    Bertindaklah sebagai jurnalis olahraga profesional dari Indonesia. 
    Saya memiliki sumber berita olahraga berbahasa Inggris berikut:
    
    - Judul Asli: {title}
    - Ringkasan/Isi: {description}
    - Waktu Rilis: {pub_date}
    
    Tugas Anda:
    Tulis ulang berita ini menjadi artikel berita olahraga berbahasa Indonesia yang panjangnya sekitar 300 kata. 
    Buat artikel yang SEO-friendly, menarik, dan informatif.
    
    Gunakan struktur Markdown berikut:
    # [Tulis Judul Artikel Baru dalam Bahasa Indonesia yang Menarik]
    
    [Paragraf Pembuka yang merangkum inti berita secara dramatis]
    
    ## [Buat Sub-heading 1 yang relevan dengan berita]
    [Isi paragraf detail karangan jurnalis berdasarkan data]
    
    ## [Buat Sub-heading 2 yang relevan dengan berita]
    [Isi paragraf detail]
    
    PENTING: Jangan tambahkan kata pengantar atau penutup dari AI (seperti "Berikut adalah artikelnya").
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        return article_content, title
    return None, None

def save_as_html(markdown_content, raw_title):
    slug = re.sub(r'[^a-zA-Z0-9]', '-', raw_title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    filename = f"{OUTPUT_DIR}/{slug}.html"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{raw_title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
            h1, h2 {{ color: #1a5276; }}
            .ad-slot {{ background: #f4f4f4; border: 1px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; color: #888; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="ad-slot">Space Iklan Adsterra 728x90</div>
        <article>{markdown_content}</article>
        <div class="ad-slot">Space Iklan Adsterra 300x250</div>
        <p><a href="/">Kembali ke Beranda</a></p>
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"V Berhasil membuat file HTML: {filename}")

def main():
    try:
        print("\nMenghubungi Sumber Berita Olahraga...")
        
        response = requests.get(RSS_URL, timeout=10)
        print(f"Status koneksi API: HTTP {response.status_code}")
        
        data = response.json()
        items = data.get('items', [])
            
        print(f"Total berita yang ditemukan: {len(items)}")
        
        if not items:
            print("PERHATIAN: Tidak ada data berita. Proses dihentikan.")
            return
            
        for item in items[:3]:
            content, title = generate_article_with_gemini(item)
            if content:
                save_as_html(content, title)
            else:
                print(f"X Gagal memproses artikel: {title}")
                
    except Exception as e:
        print(f"!!! ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
    print("\n=== SCRIPT SELESAI ===")
