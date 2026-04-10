import csv
import requests
import time
import re
import os
from dotenv import load_dotenv

# Wczytaj konfigurację z pliku .env
load_dotenv()

# Ustaw zmienne globalne (pobierane z .env)
csfloat_api_base = "https://api.csfloat.com/"
moj_klucz_api = os.getenv('CSFLOAT_KEY')

def aktualizuj_ekwipunek_csv(steam_id, steam_json):
    nazwa_pliku = f"steamid_{steam_id}.csv"

    # Wczytujemy stare dane z CSV do słownika
    stare_dane = {}
    if os.path.exists(nazwa_pliku):
        with open(nazwa_pliku, mode='r', encoding='utf-8') as plik_csv:
            reader = csv.DictReader(plik_csv)
            for wiersz in reader:
                stare_dane[wiersz['asset_id']] = wiersz
        print(f"Wczytano {len(stare_dane)} przedmiotów z lokalnego pliku CSV.")

    assets = steam_json.get('assets', [])
    descriptions = steam_json.get('descriptions', [])
    opisy_dict = {f"{d['classid']}_{d['instanceid']}": d for d in descriptions}

    nowe_wiersze_do_zapisu = []
    
    # Tworzymy folder na fotki jeśli go nie ma
    os.makedirs("images", exist_ok=True)

    print(f"\nAnalizuję {len(assets)} przedmiotów...")

    for asset in assets:
        asset_id = asset['assetid']
        klucz = f"{asset['classid']}_{asset['instanceid']}"
        desc = opisy_dict.get(klucz)

        if not desc:
            continue

        # Filtrujemy tylko to co nas interesuje
        typ_przedmiotu = desc.get('type', '')
        dozwolone_typy = ['Rifle', 'Pistol', 'Sniper', 'SMG', 'Shotgun', 'Machinegun', 'Knife', 'Gloves']
        if not any(typ in typ_przedmiotu for typ in dozwolone_typy):
            continue

        # Budujemy link do zdjęcia i parsujemy nazwę
        icon_url_code = desc.get('icon_url', '')
        pelny_link_zdjecia = f"https://community.akamai.steamstatic.com/economy/image/{icon_url_code}"
        market_name = desc.get('market_hash_name', 'Nieznany')
        stattrak = 1 if "StatTrak™" in market_name else 0
        clean_name = market_name.replace("StatTrak™ ", "").replace("★ ", "")

        if " | " in clean_name:
            bron, reszta = clean_name.split(" | ", 1)
            if "(" in reszta and ")" in reszta:
                nazwa_skina = reszta[:reszta.rfind("(")].strip()
                stan = reszta[reszta.rfind("(") + 1:reszta.rfind(")")]
            else:
                nazwa_skina = reszta
                stan = "Brak"
        else:
            bron = clean_name
            nazwa_skina = "Vanilla"
            stan = "Brak"

        # Wyciąganie naklejek z opisu
        naklejki = ""
        for d in desc.get('descriptions', []):
            val = d.get('value', '')
            if 'Sticker:' in val or 'Naklejka:' in val:
                czysty_tekst = re.sub(r'<[^>]+>', '', val)
                if "Sticker:" in czysty_tekst:
                    naklejki = czysty_tekst.split("Sticker:")[1].strip()
                elif "Naklejka:" in czysty_tekst:
                    naklejki = czysty_tekst.split("Naklejka:")[1].strip()

        # Pobieranie floata z CSFloat tylko dla nowych itemów
        if asset_id in stare_dane:
            float_value = stare_dane[asset_id]['float_value']
            pattern = stare_dane[asset_id]['pattern']
        else:
            float_value = "Brak"
            pattern = "Brak"
            inspect_url = ""

            for action in desc.get('actions', []):
                if action.get('name') == 'Inspect in Game...':
                    inspect_url = action.get('link')
                    break

            if inspect_url:
                inspect_url = inspect_url.replace("%owner_steamid%", steam_id).replace("%assetid%", asset_id)

                try:
                    # USUNIĘTO "self." - tutaj używamy zmiennych z góry pliku
                    naglowki = {
                        'Authorization': moj_klucz_api,
                        'Origin': 'https://csfloat.com',
                        'User-Agent': 'Mozilla/5.0',
                        'Accept': 'application/json'
                    }

                    # Używamy csfloat_api_base zdefiniowanego na górze
                    resp = requests.get(csfloat_api_base, params={'url': inspect_url}, headers=naglowki)

                    if resp.status_code == 200:
                        float_data = resp.json().get('iteminfo', {})
                        float_value = float_data.get('floatvalue', 'Brak')
                        pattern = float_data.get('paintseed', 'Brak')
                        print(f"Pobrano float dla: {bron} | {nazwa_skina}")
                    
                    # Sleep żeby nie dostać 429 od CSFloat
                    time.sleep(1.2)

                except Exception as e:
                    print(f"Błąd CSFloat: {e}")

        # Pobieranie zdjęcia tylko jeśli nie mamy go lokalnie
        sciezka_img = f"images/{asset_id}.png"
        if not os.path.exists(sciezka_img):
            try:
                img_response = requests.get(pelny_link_zdjecia, timeout=10)
                if img_response.status_code == 200:
                    with open(sciezka_img, 'wb') as f:
                        f.write(img_response.content)
            except:
                print(f"Nie udało się pobrać zdjęcia dla {asset_id}")

        nowe_wiersze_do_zapisu.append({
            'asset_id': asset_id,
            'bron': bron,
            'nazwa_skina': nazwa_skina,
            'stan': stan,
            'stattrak': stattrak,
            'naklejki': naklejki,
            'float_value': float_value,
            'pattern': pattern,
            'ikona_url': pelny_link_zdjecia
        })

    # Zapis całości do CSV
    naglowki_csv = ['asset_id', 'bron', 'nazwa_skina', 'stan', 'stattrak', 'naklejki', 'float_value', 'pattern', 'ikona_url']
    with open(nazwa_pliku, mode='w', newline='', encoding='utf-8') as plik_csv:
        writer = csv.DictWriter(plik_csv, fieldnames=naglowki_csv)
        writer.writeheader()
        writer.writerows(nowe_wiersze_do_zapisu)

    print(f"\nZapisano {len(nowe_wiersze_do_zapisu)} itemów do {nazwa_pliku}")