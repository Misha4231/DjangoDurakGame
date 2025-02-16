import json

from .Card import *


class Player:
    def __init__(self, name: str, player_id: str, hand=None):
        if hand is None:
            hand = []
        self.player_name: str = name
        self.__id: str = player_id

        self.__hand: list[Card] = [Card.from_string(c) for c in hand]

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

    def __eq__(self, other) -> bool:
        return self.get_id() == other.get_id() and self.get_hand() == other.get_hand() and self.player_name == other.player_name

    def __hash__(self):
        return hash(str(self))

    def to_json(self, player_id = None): # convert user data to dict
        data = {
            'id': self.get_id(),
            'name': self.get_name(),
            'hand_len': self.hands_len(),
        }
        if player_id is None or player_id == self.get_id():
            data['hand'] = [str(c) for c in self.get_hand()]

        return data

    def __str__(self):
        data = self.to_json()
        return str(data)

    @classmethod
    def from_json(cls, data: dict):
        return cls(data['name'], data['id'], data['hand'])