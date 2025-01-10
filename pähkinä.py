import requests
import time

BASE_URL = "https://koodipahkina.monad.fi/api"
API_TOKEN = "05cec097-386f-43aa-bef3-526d449636af"
MAX_NO_GAMES = 100


def is_part_of_series(current_card, card_list):
    for card_set in card_list:
        if current_card + 1 == card_set[0] or current_card - 1 == card_set[-1]:
            return True

    return False


def make_action(start_new_game, header, action=None, game_id=""):
    # Toiminnon suorittaminen epäonnistui serverimen virheeseen, virhekoodi
    # 502, joten tästä syystä toimintoa yritetään suorittaa while-loopissa.
    while True:
        if start_new_game:
            response = requests.post(f"{BASE_URL}/game", headers=header)
        else:
            response = requests.post(f"{BASE_URL}/game/{game_id}/action",
                                     headers=header,
                                     json=action)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 502:
            print(f"Virhe palvelimella, yritetään uudestaan 30 sekunnin kuluttua.")
            time.sleep(30)
        else:
            print(f"Odottamaton virhe toiminnon suorittamisessa. Syy: {response.text}")
            exit()


def strategy(state):
    current_card = state["status"]["card"]
    coins_on_table = state["status"]["money"]
    players_data = state["status"]["players"]
    my_coins = players_data[0]["money"]
    my_cards = players_data[0]["cards"]
    cards_left = state["status"]["cardsLeft"]

    print(f"Current card: {current_card}, "
          f"Coins on table: {coins_on_table}, "
          f"My coins: {my_coins}")

    if my_coins == 0:
        return {"takeCard": True}

    # Jos kortti ei täydennä sarjaa, mutta omia kolikoita on vähintään kaksi
    # kertaa
    if is_part_of_series(current_card, my_cards) is False \
            and my_coins >= cards_left * 2:
        return {"takeCard": False}

    # melko iso kortti kelpaa ensimmäiseksi kortiksi, jos mukana saa paljon kolikoita.
    if len(my_cards) == 0 and current_card < 30 and coins_on_table >= 10:
        return {"takeCard": True}

    if is_part_of_series(current_card, my_cards):
        # Tarkistetaan, että täydentääkö kortti muiden pelaajien sarjoja. Jos
        # täydentää, otetaan kortti heti.
        for player_data in players_data[1:]:
            if is_part_of_series(current_card, player_data["cards"]):
                return {"takeCard": True}

        # Jos kortti ei täydennä vastustajien sarjaa, panostetaan tällä kertaa,
        # jos kortti on verrattain iso ja vähän-panostettu, jotta saadaan
        # mahdollisesti enemmän kolikoita ensi kierroksella.
        if current_card > 10 and coins_on_table < 4:
            return {"takeCard": False}
        else:
            return {"takeCard": True}

    # Toinen korttisarja voidaan aloittaa pienellä kortilla.
    if len(my_cards) == 1 and current_card <= 10:
        return {"takeCard": True}

    # Vähäisillä kolikoilla pelataan mieluummin varman päälle, eli valitaan jo
    # ennen kolikoiden loppumista tilanteeseen nähden pieni kortti.
    if my_coins <= 2 and (current_card < 35/(my_coins + 1) or
                          (coins_on_table > 5 and current_card < 25)):
        return {"takeCard": True}

    return {"takeCard": False}


def main():
    header = {"Authorization": "Bearer " + API_TOKEN}

    status = make_action(True, header)  # Aloitetaan uusi peli
    game_id = status["gameId"]
    print(f"1. Peli (ID {game_id} on aloitettu.")
    game_counter = 1
    while True:
        if status["status"]["finished"]:
            print(f"{game_counter}. Peli (ID: {game_id}) on päättynyt.")
            game_counter += 1
            if game_counter > MAX_NO_GAMES:
                break
            status = make_action(True, header)
            game_id = status["gameId"]
            print(f"{game_counter}. Peli (ID {game_id} on aloitettu.")

        action = strategy(status)

        status = make_action(False, header, action, game_id)


if __name__ == "__main__":
    main()
