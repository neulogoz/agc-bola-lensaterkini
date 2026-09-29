import os
import random
import time
import requests
from google import genai
import json
import re
from datetime import datetime

print("=== MEMULAI SCRIPT AGC BOLA (PREMIUM UI + DYNAMIC WIDGET FIX) ===")

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
# BLOK VARIABEL AMAN (Mencegah Syntax Error Python pada Script Web)
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

SCRIPT_POPUNDER = """
<script src="https://pl31570858.profitableratecpmnetwork.com/bf/7c/c8/bf7cc8b38eeb859ad03672bf296c81ba.js"></script>
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

# SCRIPT INJEKSI KLASEMEN (Pasti Muncul)
SCRIPT_WIDGET_LOGIC = """
<script>
    const scoreAxisWidgets = {
        'ENG': { id: 'widget-atvlmumh1msi', url: 'https://widgets.scoreaxis.com/api/football/league-table/6232265abf1fa71a672159ec?widgetId=atvlmumh1msi&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=poppins&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' },
        'ESP': { id: 'widget-j7xwmumh3y7m', url: 'https://widgets.scoreaxis.com/api/football/league-table/62322c053617da0b83221cc6?widgetId=j7xwmumh3y7m&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=poppins&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' },
        'ITA': { id: 'widget-llkdmumh65vu', url: 'https://widgets.scoreaxis.com/api/football/league-table/62322b827aee66235a2be718?widgetId=llkdmumh65vu&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=poppins&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' },
        'GER': { id: 'widget-t6xvmumh55i6', url: 'https://widgets.scoreaxis.com/api/football/league-table/62321f50f7016c22d3650732?widgetId=t6xvmumh55i6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=poppins&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' },
        'FRA': { id: 'widget-bjs9mumh5ta6', url: 'https://widgets.scoreaxis.com/api/football/league-table/62322b4efd209951602c9096?widgetId=bjs9mumh5ta6&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=poppins&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' },
        'IDN': { id: 'widget-wrt7mumh7146', url: 'https://widgets.scoreaxis.com/api/football/league-table/623225c009ac1611ee0dc0f6?widgetId=wrt7mumh7146&lang=id&teamLogo=1&tableLines=0&homeAway=1&header=1&position=1&goals=1&gamesCount=1&diff=1&winCount=1&drawCount=1&loseCount=1&lastGames=1&points=1&teamsLimit=all&links=1&noFollowLinks=0&font=poppins&fontSize=14&rowDensity=100&widgetWidth=auto&widgetHeight=auto&bodyColor=%23ffffff&textColor=%23141416&linkColor=%23141416&borderColor=%23ecf1f7&tabColor=%23f3f8fd' }
    };

    function loadWidget(leagueKey) {
        let tablinks = document.getElementsByClassName("tablinks");
        for (let i = 0; i < tablinks.length; i++) { tablinks[i].classList.remove("active"); }
        if (event && event.currentTarget) {
            event.currentTarget.classList.add("active");
        } else {
            tablinks[0].classList.add("active"); // Default ke Inggris
        }

        const container = document.getElementById("dynamic-widget-container");
        const wData = scoreAxisWidgets[leagueKey];
        
        // Membersihkan kotak & menyiapkan ruang baru untuk script
        container.innerHTML = `<div id="${wData.id}" class="scoreaxis-widget" style="width: 100%; min-height: 400px; display: flex; align-items: center; justify-content: center; color: #888; font-weight: bold;">Mempersiapkan Klasemen...</div>`;
        
        // Menyuntikkan script JS secara real-time
        const scriptEl = document.createElement('script');
        scriptEl.src = wData.url;
        scriptEl.async = true;
        document.getElementById(wData.id).appendChild(scriptEl);
    }
    
    // Auto Load Liga Inggris saat web dibuka
    window.onload = function() { loadWidget('ENG'); };
</script>
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
        if(document.getElementById('page-info')) document.getElementById('page-info').innerText = `Halaman ${page} dari ${totalPages}`;
        if(document.getElementById('btn-prev')) document.getElementById('btn-prev').disabled = page === 1;
        if(document.getElementById('btn-next')) document.getElementById('btn-next').disabled = page === totalPages || totalPages === 0;
    }

    function changePage(delta) {
        currentPage += delta;
        showPage(currentPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    if(articles.length > 0) showPage(1);
</script>
"""
# =====================================================================

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
                    text = re.sub(r'
