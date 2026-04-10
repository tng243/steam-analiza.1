import api
import parser


def start_programu():
    print("--- START SKRYPTU CS2 ---")

    moje_id =api.get_steam_id()

    surowe_dane = api.ekwipunek(moje_id)

    if surowe_dane:
        parser.aktualizuj_ekwipunek_csv(moje_id, surowe_dane)
    else:
        print("Błąd: Nie można przetworzyć ekwipunku. Zamykam program.")


if __name__ == '__main__':
    start_programu()
