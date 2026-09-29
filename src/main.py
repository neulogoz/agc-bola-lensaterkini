# Ini adalah file utama untuk script scraper Python
import os
import json
import requests
import google.generativeai as genai
from datetime import datetime
import re

# ==========================================
# KONFIGURASI API
# ==========================================
# Pastikan Anda telah mengatur GEMINI_API_KEY di environment variables / secrets GitHub Actions
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY belum di-set di environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# URL endpoint utama ScoreBat Video API
SCOREBAT_API_URL = "https://www.scorebat.com/video-api/v3/feed"

# Direktori output untuk file HTML/Markdown
OUTPUT_DIR = "public/berita"

# Buat direktori jika belum ada
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# FUNGSI UTAMA
# ==========================================

def fetch_scorebat_data():
    """Mengambil data highlight bola terbaru dari ScoreBat API."""
    try:
        print("Mengambil data dari ScoreBat Video API...")
        response = requests.get(SCOREBAT_API_URL)
        response.raise_for_status()
        data = response.json()
        
        # API v3 ScoreBat mengembalikan list of objects di dalam key 'response'
        if 'response' in data and isinstance(data['response'], list):
             return data['response']
        else:
             print("Format response ScoreBat API tidak terduga.")
             return []
    except Exception as e:
        print(f"Error saat mengambil data dari ScoreBat: {e}")
        return []

def generate_article_with_gemini(match_data):
    """Menggunakan Gemini untuk menulis ulasan pertandingan singkat."""
    
    # Ekstrak data dari ScoreBat
    title = match_data.get('title', 'Pertandingan Bola')
    competition = match_data.get('competition', 'Kompetisi Tidak Diketahui')
    date_str = match_data.get('date', '')
    
    # Ambil embed iframe video (biasanya di array 'videos', ambil yang pertama)
    videos = match_data.get('videos', [])
    embed_iframe = ""
    if videos and len(videos) > 0:
        embed_iframe = videos[0].get('embed', '')
    
    print(f"Membuat artikel dengan Gemini untuk: {title}")
    
    prompt = f"""
    Bertindaklah sebagai jurnalis olahraga profesional dari Indonesia. 
    Saya memiliki data pertandingan sepak bola terbaru berikut ini:
    - Pertandingan: {title}
    - Kompetisi: {competition}
    - Tanggal: {date_str}
    
    Buatlah sebuah artikel review/highlight singkat (sekitar 300 kata) dalam Bahasa Indonesia.
    Gunakan gaya bahasa yang antusias, SEO-friendly, dan mengundang orang untuk menonton videonya.
    
    Wajib gunakan struktur Markdown berikut:
    # [Tulis Judul Artikel Menarik yang Mengandung Nama Kedua Tim]
    
    [Tulis Paragraf pembuka yang mengabarkan hasil akhir pertandingan secara dramatis]
    
    ## Jalannya Pertandingan
    [Tulis 1-2 paragraf karangan jalannya laga secara umum, fokus pada tensi laga atau momen penting]
    
    ## Video Highlight Pertandingan
    Berikut adalah cuplikan gol dan highlight dari laga sengit ini:
    
    [EMBED_VIDEO_DISINI]
    
    ## Statistik & Performa Tim
    [Tulis analisis singkat mengenai performa kedua tim di liga saat ini]
    
    PENTING: 
    1. Jangan tambahkan kata pengantar atau penutup dari AI (seperti "Berikut adalah artikelnya").
    2. Wajib pertahankan kata "[EMBED_VIDEO_DISINI]" sama persis, karena akan saya replace dengan kode asli nanti.
    """
    
    try:
        response = model.generate_content(prompt)
        article_content = response.text
        
        # Replace placeholder dengan kode iFrame asli dari ScoreBat
        article_content = article_content.replace("[EMBED_VIDEO_DISINI]", embed_iframe)
        return article_content, title
        
    except Exception as e:
        print(f"Error dari Gemini API: {e}")
        return None, None

def save_as_html(markdown_content, raw_title):
    """Menyimpan hasil markdown (yang sudah mengandung iFrame HTML) menjadi file."""
    
    # Buat slug URL dari judul pertandingan (contoh: "Arsenal - Chelsea" -> "arsenal-chelsea")
    slug = re.sub(r'[^a-zA-Z0-9]', '-', raw_title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    filename = f"{OUTPUT_DIR}/{slug}.html"
    
    # Template HTML Sederhana dengan Slot Iklan
    html_template = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{raw_title} - Lensa Terkini Bola</title>
        <style>
            body {{ font-family: 'Arial', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
            h1, h2 {{ color: #1a5276; }}
            .ad-slot {{ background: #f4f4f4; border: 1px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; color: #888; font-weight: bold; }}
            .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 20px 0; }}
            .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <div class="ad-slot">
            <!-- SLOT IKLAN ADSTERRA BANNER ATAS -->
            Space Iklan Adsterra / Banner 728x90
        </div>
        
        <!-- Artikel dari Gemini -->
        <article>
            {markdown_content}
        </article>
        
        <div class="ad-slot">
            <!-- SLOT IKLAN ADSTERRA BANNER BAWAH -->
            Space Iklan Adsterra / Banner 300x250
        </div>
        
        <p><a href="/">Kembali ke Beranda</a></p>
    </body>
    </html>
    """
    
    # Karena Gemini mereturn format Markdown text, browser tidak membacanya dengan baik jika disimpan sebagai .html langsung.
    # Untuk versi paling sederhana tanpa library Markdown tambahan di Python, kita simpan string hasil replace langsung. 
    # (Catatan: browser modern membaca tag HTML iframe di dalam teks biasa jika tidak di-escape).
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Berhasil menyimpan: {filename}")

def main():
    matches = fetch_scorebat_data()
    
    if not matches:
        print("Tidak ada pertandingan yang ditemukan atau API bermasalah.")
        return
        
    print(f"Ditemukan {len(matches)} pertandingan terbaru.")
    
    # Agar tidak menghabiskan kuota Gemini, kita proses 5 pertandingan terbaru saja setiap kali script berjalan
    for match in matches[:5]:
        article_content, raw_title = generate_article_with_gemini(match)
        
        if article_content and raw_title:
            save_as_html(article_content, raw_title)
            
    print("Selesai memproses AGC Bola.")

if __name__ == "__main__":
    main()
