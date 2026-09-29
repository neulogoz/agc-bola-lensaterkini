# Ini adalah file utama untuk script scraper Python

import os
import random
import time
import requests
from google import genai
import json
import re

print("=== MEMULAI SCRIPT AGC BOLA ===")

API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    print("ERROR: GEMINI_API_KEYS tidak ditemukan!")
    raise ValueError("GEMINI_API_KEYS belum di-set di GitHub.")

API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]
SCOREBAT_API_URL = "https://www.scorebat.com/video-api/v3/feed"
OUTPUT_DIR = "public/berita"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"API Keys berhasil di-load: {len(API_KEYS_LIST)} kunci.")

def get_gemini_response(prompt):
    random.shuffle(API_KEYS_LIST)
    for current_key in API_KEYS_LIST:
        try:
            print(f"Mencoba AI Generate dengan key: {current_key[:10]}...")
            client = genai.Client(api_key=current_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
            )
            print("-> Berhasil mendapatkan artikel dari Gemini!")
            return response.text
        except Exception as e:
            error_msg = str(e)
            print(f"-> Key gagal. Error: {error_msg}")
            if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                time.sleep(2)
                continue
            else:
                continue
    return None

def generate_article_with_gemini(match_data):
    title = match_data.get('title', 'Pertandingan Bola')
    competition = match_data.get('competition', 'Kompetisi Tidak Diketahui')
    date_str = match_data.get('date', '')
    
    videos = match_data.get('videos', [])
    embed_iframe = ""
    if videos and len(videos) > 0:
        embed_iframe = videos[0].get('embed', '')
    
    print(f"\nMemproses: {title} ({competition})")
    
    prompt = f"""
    Bertindaklah sebagai jurnalis olahraga profesional dari Indonesia. 
    Data pertandingan sepak bola:
    - Pertandingan: {title}
    - Kompetisi: {competition}
    - Tanggal: {date_str}
    
    Buatlah artikel highlight singkat (sekitar 300 kata) dalam Bahasa Indonesia.
    Gunakan struktur Markdown berikut:
    # [Tulis Judul Artikel]
    [Paragraf pembuka dramatis]
    
    ## Jalannya Pertandingan
    [Karangan 1-2 paragraf jalannya laga]
    
    ## Video Highlight Pertandingan
    Berikut adalah cuplikan golnya:
    
    [EMBED_VIDEO_DISINI]
    
    ## Statistik & Performa Tim
    [Analisis singkat performa]
    
    PENTING: Jangan tambah kata pengantar. Wajib biarkan teks [EMBED_VIDEO_DISINI] apa adanya.
    """
    
    article_content = get_gemini_response(prompt)
    
    if article_content:
        article_content = article_content.replace("[EMBED_VIDEO_DISINI]", embed_iframe)
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
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 20px 0; }}
            .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <article>{markdown_content}</article>
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"V Berhasil membuat file HTML: {filename}")

def main():
    try:
        print("\nMenghubungi ScoreBat API...")
        
        # Penambahan Header agar terbaca sebagai browser manusia (Bypass Error 403)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
        
        response = requests.get(SCOREBAT_API_URL, headers=headers, timeout=10)
        print(f"Status koneksi API: HTTP {response.status_code}")
        
        data = response.json()
        
        if isinstance(data, dict):
            matches = data.get('response', [])
        elif isinstance(data, list):
            matches = data
        else:
            matches = []
            
        print(f"Total pertandingan yang ditemukan dari API: {len(matches)}")
        
        if not matches:
            print("PERHATIAN: Tidak ada data pertandingan. Proses dihentikan.")
            return
            
        # Proses 3 pertandingan saja untuk percobaan awal
        for match in matches[:3]:
            content, title = generate_article_with_gemini(match)
            if content:
                save_as_html(content, title)
            else:
                print(f"X Gagal memproses artikel: {title}")
                
    except Exception as e:
        print(f"!!! ERROR UTAMA: {e}")

if __name__ == "__main__":
    main()
    print("\n=== SCRIPT SELESAI ===")
