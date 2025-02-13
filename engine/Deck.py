import json
from collections import deque
import random

from .Card import *

# class representing cards deck (the main one, where players take cards)
class Deck:
    def __init__(self, deck: (list[Card]) | None = None, trump: (Card | None)= None):
        if deck is None:
            self.__deck = deque() # create stack because cards are always taken from the top

            # full stack by using enums
            for suit_i in range(CardSuit.HEARTS.value, CardSuit.SPADES.value + 1):
                for rank_i in range(CardRank.SIX.value, CardRank.ACE.value + 1):
                    self.__deck.append(
                        Card(CardSuit(suit_i), CardRank(rank_i))
                    )

            random.shuffle(self.__deck) # shuffle deck
            self.__trump = self.__deck[0]  # select trump (card with most valuable suit)
        else:
            self.__deck = deque(deck)
            self.__trump = trump

    def get_trump(self) -> Card: # trump getter
        return self.__trump

    def cards_available(self) -> int: # how many cards left in deck
        return len(self.__deck)

    def take_card(self) -> Card: # take card (or nothing) from deck
        if self.cards_available() <= 0:
            raise IndexError("No cards available")

        return self.__deck.pop()

    def to_json(self):
        data = {
            'deck': list([str(c) for c in reversed(self.__deck)]),
            'trump': str(self.__trump),
        }

        return json.dumps(data)

    def __str__(self) -> str:
        data = self.to_json()
        return str(data)

    @classmethod
    def from_string(cls, data: str):
        data = json.loads(data)

        deck = data['deck']
        trump = Card.from_string(data['trump'])

        for i in range(0, len(deck)):
            deck[i] = Card.from_string(deck[i])

        return cls(deck, trump)
