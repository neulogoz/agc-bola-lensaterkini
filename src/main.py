# Ini adalah file utama untuk script scraper Python

import os
import random
import time
import requests
import google.generativeai as genai
import json
import re

# ==========================================
# KONFIGURASI ROTASI API KEY GEMINI
# ==========================================
API_KEYS_STRING = os.environ.get("GEMINI_API_KEYS")

if not API_KEYS_STRING:
    raise ValueError("GEMINI_API_KEYS belum di-set di environment variables GitHub.")

# Memecah string menjadi list API key
API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")]

# URL endpoint utama ScoreBat Video API
SCOREBAT_API_URL = "https://www.scorebat.com/video-api/v3/feed"
OUTPUT_DIR = "public/berita"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_gemini_response(prompt):
    """Mencoba generate konten dengan merotasi API Key jika terkena limit."""
    
    # Acak urutan key setiap kali fungsi dipanggil agar beban merata
    random.shuffle(API_KEYS_LIST)
    
    for current_key in API_KEYS_LIST:
        try:
            # Konfigurasi ulang Gemini dengan key yang sedang dicoba
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Eksekusi prompt
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"Key {current_key[:10]}... gagal. Error: {error_msg}")
            
            # Jika error berhubungan dengan kuota/limit, coba key berikutnya
            if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                print("Terkena limit! Beralih ke API Key selanjutnya dalam 2 detik...")
                time.sleep(2)
                continue
            else:
                # Jika error karena masalah lain (misal safety block), tetap lanjutkan ke key lain
                continue
                
    print("FATAL: Semua API Key telah dicoba dan gagal/limit.")
    return None

def generate_article_with_gemini(match_data):
    """Menggunakan Gemini untuk menulis ulasan pertandingan singkat."""
    title = match_data.get('title', 'Pertandingan Bola')
    competition = match_data.get('competition', 'Kompetisi Tidak Diketahui')
    date_str = match_data.get('date', '')
    
    videos = match_data.get('videos', [])
    embed_iframe = ""
    if videos and len(videos) > 0:
        embed_iframe = videos[0].get('embed', '')
    
    print(f"\nMembuat artikel untuk: {title}")
    
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
    
    PENTING: Jangan tambahkan kata pengantar atau penutup dari AI. Wajib biarkan teks [EMBED_VIDEO_DISINI] apa adanya.
    """
    
    # Gunakan fungsi rotasi yang baru dibuat
    article_content = get_gemini_response(prompt)
    
    if article_content:
        article_content = article_content.replace("[EMBED_VIDEO_DISINI]", embed_iframe)
        return article_content, title
    else:
        return None, None
