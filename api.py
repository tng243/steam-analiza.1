import requests
import re  # Nowa biblioteka wbudowana w Pythona, do wyszukiwania tekstu


def get_steam_id(link):  # <-- zmiana: link jako argument zamiast input()
    link = link.strip()

    # 1. SCENARIUSZ: Zwykły link z cyframi (/profiles/)
    if '/profiles/' in link:
        czyszczenie_linku = link.rstrip('/').split('/')
        steamid = czyszczenie_linku[-1]

    # 2. SCENARIUSZ: Niestandardowy link z nazwą (/id/)
    elif '/id/' in link:
        print("Wykryto niestandardowy link. Rozszyfrowuję prawdziwe SteamID64...")

        # Doklejamy nasz magiczny dopisek do linku
        url_xml = link.rstrip('/') + "/?xml=1"

        try:
            resp = requests.get(url_xml)
            if resp.status_code == 200:
                # Szukamy tagu <steamID64> i wyciągamy z niego same cyfry
                szukane_id = re.search(r'<steamID64>(\d+)</steamID64>', resp.text)
                if szukane_id:
                    steamid = szukane_id.group(1)  # Zapisujemy znalezione cyfry
                else:
                    print("Błąd: Nie znaleziono ID na tym profilu. Sprawdź, czy link jest poprawny.")
                    return None
            else:
                print(f"Błąd przy odczytywaniu ID. Kod: {resp.status_code}")
                return None
        except Exception as e:
            print(f"Błąd połączenia ze Steamem: {e}")
            return None

    # 3. SCENARIUSZ: Ktoś wkleił jakieś głupoty
    else:
        print("Błąd: Link musi zawierać /profiles/ albo /id/ !")
        return None

    print(f"Prawdziwe 17-cyfrowe Steam ID to: {steamid}")
    return steamid


# dostęp do eq (zostaje bez zmian)
def ekwipunek(steamid):
    url = f"https://steamcommunity.com/inventory/{steamid}/730/2"
    parser = {'l': 'english'}
    print('Łączenie z serwerami steam...')

    try:
        response = requests.get(url, params=parser)
        if response.status_code == 200:
            print('Połączono z serwerami steam!')
            dane = response.json()
            ilosc_przedmiotow = len(dane.get('assets', []))
            print(f'Znaleziono {ilosc_przedmiotow} przedmiotów w ekwipunku.')
            return dane

        elif response.status_code == 403:
            print('Błąd: Ekwipunek jest prywatny!')
        else:
            print(f'Błąd połączenia. Kod statusu: {response.status_code}')

    except requests.exceptions.RequestException as e:
        print(f'Błąd połączenia z internetem lub serwerami steam: {e}')
