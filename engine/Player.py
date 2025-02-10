from Card import *


class Player:
    def __init__(self, name: str, player_id: str):
        self.player_name: str = name
        self.__id: str = player_id

        self.__hand: list[Card] = []

    def get_id(self) -> str:
        return self.__id

    def get_name(self) -> str:
        return self.player_name

    def get_hand(self) -> list[Card]:
        return self.__hand

    def hands_len(self) -> int:
        return len(self.__hand)

    def take_card(self, card: Card):
        self.__hand.append(card)

    def throw_card(self, card: Card):
        self.__hand.remove(card)

    def have_card(self, card: Card) -> bool:
        return card in self.__hand