from enum import Enum

# helper enums for Card class
class CardSuit(Enum):
    HEARTS = 1
    CLUBS = 2
    DIAMONDS = 3
    SPADES = 4

class CardRank(Enum):  # only six-ace because classical Durak don't use two-five
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

# class representing game card
class Card:
    str_separator = '_'

    def __init__(self, suit: CardSuit, rank: CardRank):
        self.__suit: CardSuit = suit # set the private suit field
        self.__rank: CardRank = rank # set the private rank field

    def get_suit(self): # suit getter
        return self.__suit

    def get_rank(self): # rank getter
        return self.__rank

    def __str__(self): #string representation (match names of card images)
        return f"{self.__rank.name}_{self.__suit.name}"

    @classmethod
    def from_string(cls, str_representation: str): # construct card from string representation
        str_representation = str_representation.upper()

        if Card.str_separator not in str_representation: # check if string is valid
            raise ValueError("Invalid string representation")

        parts = str_representation.split(Card.str_separator) #split into 2 parts
        if len(parts) != 2: #validate
            raise ValueError("Invalid string representation")

        rank = parts[0]
        suit = parts[1]

        return cls(CardSuit(CardSuit[suit]), CardRank(CardRank[rank])) # call constructor with enum values