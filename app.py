from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import os
import requests
import json
import os
import sqlite3
from datetime import datetime
import socket
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile access

# Database setup for favorites
def init_db():
    conn = sqlite3.connect('nerv9_radio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS favorites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  station_uuid TEXT,
                  station_name TEXT,
                  station_url TEXT,
                  country TEXT,
                  language TEXT,
                  tags TEXT,
                  favicon TEXT,
                  added_date TEXT)''')
    conn.commit()
    conn.close()

# Backup radio stations when radio-browser.info is down
BACKUP_STATIONS = [
    {
        'uuid': 'backup-1',
        'name': 'BBC Radio 1',
        'url': 'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one',
        'country': 'United Kingdom',
        'language': 'english',
        'tags': 'pop,rock,dance',
        'favicon': '',
        'bitrate': 128,
        'codec': 'MP3',
        'votes': 1000
    },
    {
        'uuid': 'backup-2',
        'name': 'NPR News',
        'url': 'https://npr-ice.streamguys1.com/live.mp3',
        'country': 'United States',
        'language': 'english',
        'tags': 'news,talk',
        'favicon': '',
        'bitrate': 128,
        'codec': 'MP3',
        'votes': 900
    },
    {
        'uuid': 'backup-3',
        'name': 'Jazz24',
        'url': 'https://live.wostreaming.net/direct/ppm-jazz24mp3-ibc3',
        'country': 'United States',
        'language': 'english',
        'tags': 'jazz,smooth jazz',
        'favicon': '',
        'bitrate': 128,
        'codec': 'MP3',
        'votes': 800
    },
    {
        'uuid': 'backup-4',
        'name': 'Classic Rock Florida',
        'url': 'https://playerservices.streamtheworld.com/api/livestream-redirect/WJRR_FM.mp3',
        'country': 'United States',
        'language': 'english',
        'tags': 'rock,classic rock',
        'favicon': '',
        'bitrate': 128,
        'codec': 'MP3',
        'votes': 700
    },
    {
        'uuid': 'backup-5',
        'name': 'SomaFM Groove Salad',
        'url': 'https://somafm.com/groovesalad256.pls',
        'country': 'United States',
        'language': 'english',
        'tags': 'ambient,electronic,chill',
        'favicon': '',
        'bitrate': 256,
        'codec': 'MP3',
        'votes': 600
    },
    {
        'uuid': 'backup-6',
        'name': 'Radio Paradise',
        'url': 'http://stream.radioparadise.com/aac-320',
        'country': 'United States',
        'language': 'english',
        'tags': 'eclectic,alternative',
        'favicon': '',
        'bitrate': 320,
        'codec': 'AAC',
        'votes': 500
    },
    {
        'uuid': 'backup-7',
        'name': '181.FM The Buzz',
        'url': 'http://listen.181fm.com/181-buzz_128k.mp3',
        'country': 'United States',
        'language': 'english',
        'tags': 'alternative,grunge,90s',
        'favicon': '',
        'bitrate': 128,
        'codec': 'MP3',
        'votes': 400
    },
    {
        'uuid': 'backup-8',
        'name': 'KEXP 90.3 FM',
        'url': 'https://kexp-mp3-128.streamguys1.com/kexp128.mp3',
        'country': 'United States',
        'language': 'english',
        'tags': 'indie,alternative,rock',
        'favicon': '',
        'bitrate': 128,
        'codec': 'MP3',
        'votes': 300
    }
]

# Get available radio-browser.info servers
def get_radio_browser_servers():
    # Try the specific working server first, then fallback to main API
    return [
        "https://de2.api.radio-browser.info",
        "https://api.radio-browser.info"
    ]

# Headers for radio-browser.info API
HEADERS = {
    'User-Agent': 'NERV9-Radio/1.0'
}

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NERV9 RADIO</title>
    <meta name="theme-color" content="#000000">
    <link rel="manifest" href="/manifest.json">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #000000; color: #dc2626; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; overflow-x: hidden; min-height: 100vh; }
        .container { max-width: 100%; padding: 20px; min-height: 100vh; }
        .header { text-align: center; margin-bottom: 30px; padding: 20px 0; border-bottom: 2px solid #dc2626; }
        .logo { font-size: 2.5rem; font-weight: 900; letter-spacing: 3px; margin-bottom: 5px; text-shadow: 0 0 20px rgba(220, 38, 38, 0.5); }
        .subtitle { font-size: 0.9rem; opacity: 0.7; letter-spacing: 2px; }
        .search-container { margin-bottom: 30px; position: relative; }
        .search-input { width: 100%; padding: 15px 20px; background: #111; border: 2px solid #333; border-radius: 25px; color: #dc2626; font-size: 16px; transition: all 0.3s ease; }
        .search-input:focus { outline: none; border-color: #dc2626; box-shadow: 0 0 20px rgba(220, 38, 38, 0.3); }
        .search-input::placeholder { color: #666; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .btn { padding: 10px 20px; background: #dc2626; color: #000; border: none; border-radius: 20px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; font-size: 14px; }
        .btn:hover { background: #b91c1c; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(220, 38, 38, 0.3); }
        .player { background: #111; border-radius: 15px; padding: 20px; margin-bottom: 30px; border: 1px solid #333; }
        .now-playing { text-align: center; margin-bottom: 20px; }
        .station-name { font-size: 1.2rem; font-weight: bold; margin-bottom: 5px; }
        .station-info { font-size: 0.9rem; opacity: 0.7; }
        .player-controls { display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 15px; }
        .play-btn { width: 60px; height: 60px; border-radius: 50%; background: #dc2626; color: #000; border: none; font-size: 24px; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; }
        .play-btn:hover { background: #b91c1c; transform: scale(1.1); }
        .volume-container { display: flex; align-items: center; gap: 10px; justify-content: center; }
        .volume-slider { width: 100px; height: 4px; background: #333; outline: none; border-radius: 2px; -webkit-appearance: none; }
        .volume-slider::-webkit-slider-thumb { appearance: none; width: 16px; height: 16px; background: #dc2626; border-radius: 50%; cursor: pointer; }
        .tabs { display: flex; margin-bottom: 20px; background: #111; border-radius: 25px; padding: 5px; }
        .tab { flex: 1; padding: 10px; text-align: center; cursor: pointer; border-radius: 20px; transition: all 0.3s ease; font-size: 14px; }
        .tab.active { background: #dc2626; color: #000; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .section-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 15px; text-align: center; text-transform: uppercase; letter-spacing: 1px; }
        .stations-list { margin-bottom: 20px; }
        .station-item { background: #111; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #333; cursor: pointer; transition: all 0.3s ease; display: flex; justify-content: space-between; align-items: center; }
        .station-item:hover { border-color: #dc2626; background: #1a1a1a; }
        .station-details h3 { font-size: 1rem; margin-bottom: 5px; }
        .station-details p { font-size: 0.8rem; opacity: 0.7; }
        .station-actions { display: flex; gap: 10px; align-items: center; }
        .favorite-btn { width: 40px; height: 40px; border-radius: 50%; background: transparent; border: 2px solid #333; color: #666; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; font-size: 18px; }
        .favorite-btn.favorited { border-color: #dc2626; color: #dc2626; }
        .favorite-btn:hover { border-color: #dc2626; color: #dc2626; }
        .loading { text-align: center; padding: 20px; opacity: 0.7; }
        .error { text-align: center; padding: 20px; color: #dc2626; background: #2a1515; border-radius: 10px; margin: 10px 0; }
        .status { position: fixed; bottom: 20px; right: 20px; background: #dc2626; color: #000; padding: 10px 15px; border-radius: 20px; font-size: 12px; z-index: 1000; opacity: 0; transform: translateY(50px); transition: all 0.3s ease; }
        .status.show { opacity: 1; transform: translateY(0); }
        @media (max-width: 768px) { .container { padding: 15px; } .logo { font-size: 2rem; } .controls { justify-content: center; } .btn { font-size: 12px; padding: 8px 16px; } }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">NERV9</div>
            <div class="subtitle">RADIO TERMINAL</div>
        </header>
        <div class="search-container">
            <input type="text" class="search-input" placeholder="Search radio stations..." id="searchInput">
        </div>
        <div class="controls">
            <button class="btn" id="searchBtn">Search</button>
            <button class="btn" id="popularBtn">Popular</button>
            <button class="btn" id="clearBtn">Clear</button>
        </div>
        <div class="player">
            <div class="now-playing">
                <div class="station-name" id="currentStation">No Station Selected</div>
                <div class="station-info" id="currentInfo">Select a station to begin</div>
            </div>
            <div class="player-controls">
                <button class="play-btn" id="playBtn">▶</button>
            </div>
            <div class="volume-container">
                <span>🔈</span>
                <input type="range" class="volume-slider" id="volumeSlider" min="0" max="100" value="50">
                <span>🔊</span>
            </div>
        </div>
        <div class="tabs">
            <div class="tab active" id="stationsTab">Stations</div>
            <div class="tab" id="favoritesTab">Favorites</div>
        </div>
        <div class="tab-content active" id="stationsContent">
            <div class="section-title">Radio Stations</div>
            <div class="stations-list" id="stationsList">
                <div class="loading">Search for stations or browse popular ones</div>
            </div>
        </div>
        <div class="tab-content" id="favoritesContent">
            <div class="section-title">Your Favorites</div>
            <div class="stations-list" id="favoritesList">
                <div class="loading">No favorites yet</div>
            </div>
        </div>
    </div>
    <div class="status" id="status"></div>
    <audio id="audioPlayer" preload="none"></audio>
    <script>
        const API_BASE = window.location.origin;
        const USER_ID = 'user_' + Math.random().toString(36).substr(2, 9);
        let currentStationData = null; let isPlaying = false; let stations = []; let favorites = [];
        document.addEventListener('DOMContentLoaded', function() { loadFavorites(); setupEventListeners(); loadPopularStations(); });
        function setupEventListeners() {
            document.getElementById('searchBtn').addEventListener('click', searchStations);
            document.getElementById('popularBtn').addEventListener('click', loadPopularStations);
            document.getElementById('clearBtn').addEventListener('click', clearStations);
            document.getElementById('playBtn').addEventListener('click', togglePlay);
            document.getElementById('volumeSlider').addEventListener('input', setVolume);
            document.getElementById('searchInput').addEventListener('keypress', function(e) { if (e.key === 'Enter') searchStations(); });
            document.getElementById('stationsTab').addEventListener('click', () => switchTab('stations'));
            document.getElementById('favoritesTab').addEventListener('click', () => switchTab('favorites'));
            const audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.addEventListener('loadstart', () => showStatus('Loading...'));
            audioPlayer.addEventListener('canplay', () => showStatus('Ready to play'));
            audioPlayer.addEventListener('playing', () => showStatus('Playing'));
            audioPlayer.addEventListener('pause', () => showStatus('Paused'));
            audioPlayer.addEventListener('error', () => showStatus('Error loading stream'));
        }
        function switchTab(tab) {
            if (tab === 'stations') {
                document.getElementById('stationsTab').classList.add('active');
                document.getElementById('favoritesTab').classList.remove('active');
                document.getElementById('stationsContent').classList.add('active');
                document.getElementById('favoritesContent').classList.remove('active');
            } else {
                document.getElementById('favoritesTab').classList.add('active');
                document.getElementById('stationsTab').classList.remove('active');
                document.getElementById('favoritesContent').classList.add('active');
                document.getElementById('stationsContent').classList.remove('active');
            }
        }
        async function searchStations() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) { showStatus('Please enter a search term'); return; }
            showLoading(document.getElementById('stationsList'));
            try {
                const response = await fetch(`${API_BASE}/api/stations/search?q=${encodeURIComponent(query)}&limit=20`);
                const data = await response.json();
                if (data.stations && data.stations.length > 0) {
                    stations = data.stations; renderStations(stations); showStatus(`Found ${data.count} stations`);
                } else {
                    document.getElementById('stationsList').innerHTML = '<div class="error">No stations found</div>'; showStatus('No stations found');
                }
            } catch (error) {
                document.getElementById('stationsList').innerHTML = '<div class="error">Error searching stations</div>'; showStatus('Search failed');
            }
        }
        async function loadPopularStations() {
            showLoading(document.getElementById('stationsList'));
            try {
                const response = await fetch(`${API_BASE}/api/stations/popular?limit=20`);
                const data = await response.json();
                if (data.stations && data.stations.length > 0) {
                    stations = data.stations; renderStations(stations); showStatus('Popular stations loaded');
                } else {
                    document.getElementById('stationsList').innerHTML = '<div class="error">No popular stations available</div>';
                }
            } catch (error) {
                document.getElementById('stationsList').innerHTML = '<div class="error">Error loading popular stations</div>'; showStatus('Failed to load popular stations');
            }
        }
        function renderStations(stationsList_data) {
            document.getElementById('stationsList').innerHTML = stationsList_data.map(station => `
                <div class="station-item" onclick="selectStation('${station.uuid}')">
                    <div class="station-details">
                        <h3>${station.name}</h3>
                        <p>${station.country} • ${station.language} • ${station.bitrate}k</p>
                        <p>${station.tags}</p>
                    </div>
                    <div class="station-actions">
                        <button class="favorite-btn ${isFavorite(station.uuid) ? 'favorited' : ''}" 
                                onclick="event.stopPropagation(); toggleFavorite('${station.uuid}')">♥</button>
                    </div>
                </div>
            `).join('');
        }
        async function selectStation(uuid) {
            const station = stations.find(s => s.uuid === uuid) || favorites.find(f => f.station_uuid === uuid);
            if (!station) return;
            currentStationData = station;
            document.getElementById('currentStation').textContent = station.name || station.station_name;
            document.getElementById('currentInfo').textContent = `${station.country} • ${station.language}`;
            try {
                await fetch(`${API_BASE}/api/stations/click`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ uuid: station.uuid || station.station_uuid })
                });
            } catch (error) { console.log('Failed to record click'); }
            document.getElementById('audioPlayer').src = station.url || station.station_url;
            document.getElementById('audioPlayer').load();
            showStatus('Station selected');
        }
        function togglePlay() {
            if (!currentStationData) { showStatus('Please select a station first'); return; }
            const audioPlayer = document.getElementById('audioPlayer');
            const playBtn = document.getElementById('playBtn');
            if (isPlaying) { audioPlayer.pause(); playBtn.textContent = '▶'; isPlaying = false; }
            else { audioPlayer.play(); playBtn.textContent = '⏸'; isPlaying = true; }
        }
        function setVolume() {
            const volume = document.getElementById('volumeSlider').value / 100;
            const audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.volume = volume;
            console.log('Volume set to:', volume);
        }
        async function toggleFavorite(uuid) {
            const station = stations.find(s => s.uuid === uuid);
            if (!station) return;
            if (isFavorite(uuid)) {
                try {
                    const favorite = favorites.find(f => f.station_uuid === uuid);
                    const response = await fetch(`${API_BASE}/api/favorites/${favorite.id}?user_id=${USER_ID}`, { method: 'DELETE' });
                    if (response.ok) { favorites = favorites.filter(f => f.station_uuid !== uuid); renderFavorites(); showStatus('Removed from favorites'); }
                } catch (error) { showStatus('Failed to remove favorite'); }
            } else {
                try {
                    const response = await fetch(`${API_BASE}/api/favorites`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: USER_ID, station_uuid: station.uuid, station_name: station.name,
                            station_url: station.url, country: station.country, language: station.language,
                            tags: station.tags, favicon: station.favicon
                        })
                    });
                    if (response.ok) { loadFavorites(); showStatus('Added to favorites'); }
                } catch (error) { showStatus('Failed to add favorite'); }
            }
            renderStations(stations);
        }
        async function loadFavorites() {
            try {
                const response = await fetch(`${API_BASE}/api/favorites?user_id=${USER_ID}`);
                const data = await response.json(); favorites = data.favorites || []; renderFavorites();
            } catch (error) { console.log('Failed to load favorites'); }
        }
        function renderFavorites() {
            if (favorites.length === 0) {
                document.getElementById('favoritesList').innerHTML = '<div class="loading">No favorites yet</div>'; return;
            }
            document.getElementById('favoritesList').innerHTML = favorites.map(favorite => `
                <div class="station-item" onclick="selectFavoriteStation('${favorite.station_uuid}')">
                    <div class="station-details">
                        <h3>${favorite.station_name}</h3>
                        <p>${favorite.country} • ${favorite.language}</p>
                        <p>${favorite.tags}</p>
                    </div>
                    <div class="station-actions">
                        <button class="favorite-btn favorited" onclick="event.stopPropagation(); removeFavorite(${favorite.id})">♥</button>
                    </div>
                </div>
            `).join('');
        }
        function selectFavoriteStation(uuid) {
            const favorite = favorites.find(f => f.station_uuid === uuid); if (!favorite) return;
            currentStationData = { uuid: favorite.station_uuid, name: favorite.station_name, url: favorite.station_url, country: favorite.country, language: favorite.language };
            document.getElementById('currentStation').textContent = favorite.station_name;
            document.getElementById('currentInfo').textContent = `${favorite.country} • ${favorite.language}`;
            document.getElementById('audioPlayer').src = favorite.station_url; document.getElementById('audioPlayer').load();
            showStatus('Favorite station selected');
        }
        async function removeFavorite(favoriteId) {
            try {
                const response = await fetch(`${API_BASE}/api/favorites/${favoriteId}?user_id=${USER_ID}`, { method: 'DELETE' });
                if (response.ok) { favorites = favorites.filter(f => f.id !== favoriteId); renderFavorites(); renderStations(stations); showStatus('Removed from favorites'); }
            } catch (error) { showStatus('Failed to remove favorite'); }
        }
        function isFavorite(uuid) { return favorites.some(f => f.station_uuid === uuid); }
        function clearStations() { document.getElementById('stationsList').innerHTML = '<div class="loading">Search for stations or browse popular ones</div>'; stations = []; showStatus('Stations cleared'); }
        function showLoading(element) { element.innerHTML = '<div class="loading">Loading...</div>'; }
        function showStatus(message) {
            const status = document.getElementById('status'); status.textContent = message; status.classList.add('show');
            setTimeout(() => { status.classList.remove('show'); }, 3000);
        }
        setVolume();
    </script>
</body>
</html>'''

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "NERV9 RADIO",
        "short_name": "NERV9",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#000000",
        "theme_color": "#dc2626",
        "icons": [
            {
                "src": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgZmlsbD0ibm9uZSIgdmlld0JveD0iMCAwIDMyIDMyIj48cGF0aCBmaWxsPSIjZGMyNjI2IiBkPSJNMTYgMmExNCAxNCAwIDAgMC0xNCAxNHY2YTE1IDE1IDAgMCAwIDE1IDE1aDNhMTQgMTQgMCAwIDAgMTMtMTRWMTZBMTMgMTMgMCAwIDAgMzEgNEgxNmExNCAxNCAwIDAgMC0xNCAxNHYyYTE1IDE1IDAgMCAwIDE1IDE1aDNhMTQgMTQgMCAwIDAgMTMtMTRWMTZBMTYgMTYgMCAwIDAgMzEgNEgxNnoiLz48L3N2Zz4=",
                "sizes": "192x192",
                "type": "image/svg+xml"
            },
            {
                "src": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNTEyIiBoZWlnaHQ9IjUxMiIgZmlsbD0ibm9uZSIgdmlld0JveD0iMCAwIDMyIDMyIj48cGF0aCBmaWxsPSIjZGMyNjI2IiBkPSJNMTYgMmExNCAxNCAwIDAgMC0xNCAxNHY2YTE1IDE1IDAgMCAwIDE1IDE1aDNhMTQgMTQgMCAwIDAgMTMtMTRWMTZBMTMgMTMgMCAwIDAgMzEgNEgxNmExNCAxNCAwIDAgMC0xNCAxNHYyYTE1IDE1IDAgMCAwIDE1IDE1aDNhMTQgMTQgMCAwIDAgMTMtMTRWMTZBMTYgMTYgMCAwIDAgMzEgNEgxNnoiLz48L3N2Zz4=",
                "sizes": "512x512",
                "type": "image/svg+xml"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    return '''
const CACHE_NAME = 'nerv9-radio-v1';
const urlsToCache = [
    '/',
    '/manifest.json'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});
''', {'Content-Type': 'application/javascript'}

@app.route('/api/stations/search', methods=['GET'])
def search_stations():
    """Search radio stations"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 50, type=int)
    
    if not query:
        return jsonify({"error": "Search query required"}), 400
    
    servers = get_radio_browser_servers()
    print(f"🔍 Searching for '{query}' on {len(servers)} servers...")
    
    for i, server in enumerate(servers):
        try:
            print(f"⏳ Trying server {i+1}: {server}")
            
            # Use the search endpoint instead of byname
            url = f"{server}/json/stations/search"
            params = {
                'name': query,
                'limit': limit,
                'hidebroken': 'true',
                'order': 'votes',
                'reverse': 'true'
            }
            
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                stations = response.json()
                print(f"✅ Found {len(stations)} stations")
                
                # Clean and format the response
                formatted_stations = []
                for station in stations:
                    # Only include stations with working URLs
                    if station.get('url') and station.get('name'):
                        formatted_stations.append({
                            'uuid': station.get('stationuuid', ''),
                            'name': station.get('name', 'Unknown Station'),
                            'url': station.get('url', ''),
                            'country': station.get('country', ''),
                            'language': station.get('language', ''),
                            'tags': station.get('tags', ''),
                            'favicon': station.get('favicon', ''),
                            'bitrate': station.get('bitrate', 0),
                            'codec': station.get('codec', ''),
                            'votes': station.get('votes', 0)
                        })
                
                print(f"🎵 Returning {len(formatted_stations)} valid stations")
                return jsonify({
                    "stations": formatted_stations,
                    "count": len(formatted_stations)
                })
                
        except Exception as e:
            print(f"❌ Server {server} failed: {str(e)}")
            continue
    
    # Fallback to searching backup stations if API is down
    print(f"🔄 Radio-browser.info is down, searching backup stations for '{query}'")
    query_lower = query.lower()
    matching_stations = []
    
    for station in BACKUP_STATIONS:
        if (query_lower in station['name'].lower() or 
            query_lower in station['tags'].lower()):
            matching_stations.append(station)
    
    if not matching_stations:
        # If no matches, return all backup stations
        matching_stations = BACKUP_STATIONS
    
    result_limit = min(limit, len(matching_stations))
    return jsonify({
        "stations": matching_stations[:result_limit],
        "count": result_limit
    })

@app.route('/api/stations/popular', methods=['GET'])
def popular_stations():
    """Get popular stations"""
    limit = request.args.get('limit', 20, type=int)
    
    servers = get_radio_browser_servers()
    print(f"🔥 Loading popular stations from {len(servers)} servers...")
    
    for i, server in enumerate(servers):
        try:
            print(f"⏳ Trying server {i+1}: {server}")
            url = f"{server}/json/stations/topvote"
            params = {
                'limit': limit,
                'hidebroken': 'true'
            }
            
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                stations = response.json()
                print(f"✅ Found {len(stations)} popular stations")
                
                formatted_stations = []
                for station in stations:
                    if station.get('url') and station.get('name'):
                        formatted_stations.append({
                            'uuid': station.get('stationuuid', ''),
                            'name': station.get('name', 'Unknown Station'),
                            'url': station.get('url', ''),
                            'country': station.get('country', ''),
                            'language': station.get('language', ''),
                            'tags': station.get('tags', ''),
                            'favicon': station.get('favicon', ''),
                            'bitrate': station.get('bitrate', 0),
                            'codec': station.get('codec', ''),
                            'votes': station.get('votes', 0)
                        })
                
                print(f"🎵 Returning {len(formatted_stations)} valid stations")
                return jsonify({
                    "stations": formatted_stations,
                    "count": len(formatted_stations)
                })
                
        except Exception as e:
            print(f"❌ Server {server} failed: {str(e)}")
            continue
    
    # Fallback to backup stations if API is down
    print("🔄 Radio-browser.info is down, using backup stations")
    backup_limit = min(limit, len(BACKUP_STATIONS))
    return jsonify({
        "stations": BACKUP_STATIONS[:backup_limit],
        "count": backup_limit
    })

@app.route('/api/stations/click', methods=['POST'])
def click_station():
    """Record a station click to radio-browser.info"""
    data = request.get_json()
    station_uuid = data.get('uuid')
    
    if not station_uuid:
        return jsonify({"error": "Station UUID required"}), 400
    
    servers = get_radio_browser_servers()
    
    for server in servers:
        try:
            url = f"{server}/json/url/{station_uuid}"
            response = requests.get(url, headers=HEADERS, timeout=5)
            
            if response.status_code == 200:
                return jsonify({"success": True, "message": "Click recorded"})
                
        except Exception as e:
            continue
    
    return jsonify({"success": False, "message": "Unable to record click"})

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """Get user favorites"""
    user_id = request.args.get('user_id', 'default_user')
    
    conn = sqlite3.connect('nerv9_radio.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM favorites WHERE user_id=? ORDER BY added_date DESC", (user_id,))
    favorites = c.fetchall()
    
    conn.close()
    
    formatted_favorites = []
    for fav in favorites:
        formatted_favorites.append({
            'id': fav[0],
            'station_uuid': fav[2],
            'station_name': fav[3],
            'station_url': fav[4],
            'country': fav[5],
            'language': fav[6],
            'tags': fav[7],
            'favicon': fav[8],
            'added_date': fav[9]
        })
    
    return jsonify({
        "favorites": formatted_favorites,
        "count": len(formatted_favorites)
    })

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """Add station to favorites"""
    data = request.get_json()
    user_id = data.get('user_id', 'default_user')
    
    required_fields = ['station_uuid', 'station_name', 'station_url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400
    
    conn = sqlite3.connect('nerv9_radio.db')
    c = conn.cursor()
    
    # Check if already exists
    c.execute("SELECT id FROM favorites WHERE user_id=? AND station_uuid=?", 
              (user_id, data['station_uuid']))
    
    if c.fetchone():
        conn.close()
        return jsonify({"error": "Station already in favorites"}), 409
    
    # Add new favorite
    c.execute("""INSERT INTO favorites 
                 (user_id, station_uuid, station_name, station_url, country, language, tags, favicon, added_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (user_id, data['station_uuid'], data['station_name'], data['station_url'],
               data.get('country', ''), data.get('language', ''), data.get('tags', ''),
               data.get('favicon', ''), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Station added to favorites"})

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
def remove_favorite(favorite_id):
    """Remove station from favorites"""
    user_id = request.args.get('user_id', 'default_user')
    
    conn = sqlite3.connect('nerv9_radio.db')
    c = conn.cursor()
    
    c.execute("DELETE FROM favorites WHERE id=? AND user_id=?", (favorite_id, user_id))
    
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "Favorite not found"}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Favorite removed"})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "NERV9 Radio Backend"
    })

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Get port from environment variable (for deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the server
    print("🎵 NERV9 RADIO Backend Starting...")
    print("📡 Checking radio-browser.info connectivity...")
    
    servers = get_radio_browser_servers()
    print(f"✅ Found {len(servers)} radio-browser.info servers")
    
    app.run(host='0.0.0.0', port=port, debug=False)
