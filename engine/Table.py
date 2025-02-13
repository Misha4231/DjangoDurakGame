import json

from .Deck import *
from .Player import *

class Table:
    def __init__(self, players: list[Player]):
        self.deck = Deck() # deck laying on table

        if len(players) < 2 or len(players) > 4: # validate players count
            raise ValueError("Table needs at least 2 and at most 4 players.")

        self.players: list[Player] = players # list of players
        self.winners: list[Player] = [] # players left with no cards (while deck is also empty)
        self.attack_state: dict[Card, (Card | None)] = dict() # attack state represent cards laying on table when player attacks another one. Visually, to "beat" card, the player have to put higher value card on top of bottom one
        self.attacks_number: int = 0 # the number of attacks was made
        self.refill_players_order: dict[Player, None] = dict() # ordered set to keep track of throwing order to properly refill cards after attack

        # give every player 6 cards at the beginning
        for player in self.players:
            for _ in range(0, 6):
                player.take_card(self.deck.take_card())

        # select player who plays turn first (the one with the least ranked trump card)
        self.__turn = 0  # default first player
        self.trump_suit = self.deck.get_trump().get_suit()
        least_trump = None  # Track the lowest trump card rank
        turn_candidate = None  # Track which player has the lowest trump card

        for playerIdx, player in enumerate(self.players):
            for card in player.get_hand():
                if card.get_suit() == self.trump_suit:
                    if least_trump is None or card.get_rank().value < least_trump.value:
                        least_trump = card.get_rank()
                        turn_candidate = playerIdx

        # If a player with a trump card was found, assign turn to them
        if turn_candidate is not None:
            self.__turn = turn_candidate

    def get_turn(self) -> int: # get playing player index
        return self.__turn

    def get_next_turn(self) -> int: # get the next player after playing one
        if len(self.players) - 1 == self.__turn: # if index is on the end go at the start
            return 0

        return self.__turn + 1

    def play_turn(self, card: Card): # play turn (player with index self.__turn)
        player = self.players[self.__turn]
        if not player.have_card(card): # validate if user actually have given card in hand
            raise ValueError("Cannot play a card that is not in player's hand.")

        # put card on table
        player.throw_card(card)
        self.attack_state[card] = None

        self.refill_players_order[player] = None # store order to properly refill cards

        self.attacks_number += 1

    def defend(self, bottom_card: Card, defender_card: Card): # defender should defend from cards given to him (or take them)
        defender = self.players[self.get_next_turn()]
        if not defender.have_card(defender_card):  # validate if user actually have given card in hand
            raise ValueError("Cannot play a card that is not in player's hand.")

        if bottom_card not in self.attack_state: # check if bottom card is on the table
            raise ValueError("Cannot beat non existing card.")
        if self.attack_state[bottom_card] is not None: # check if card wasn't previously beaten
            raise ValueError("Cannot beat card that is already beaten.")

        # check if the defender card is higher (in current hierarchy) then the bottom one
        if defender_card.get_suit() == bottom_card.get_suit():
            if defender_card.get_rank().value < bottom_card.get_rank().value:
                raise ValueError("Defender card has lower rank than the bottom one.")
        elif defender_card.get_suit() != self.trump_suit and bottom_card.get_suit() == self.trump_suit:
            raise ValueError("Can't beat trump suited card with no trump card.")

        # put card on table
        defender.throw_card(defender_card)
        self.attack_state[bottom_card] = defender_card

    def throw_additional(self, throwing_player_id: str, card: Card): # players can throw more cards with the same suit as was before in the attack to defender
        defender = self.players[self.get_next_turn()]
        if defender.get_id() == throwing_player_id: # check if defender and player throwing card have the same id's
            raise ValueError("Defender cannot throw additional cards.")

        # according to rules, number of cards in one attack can't be more than number of cards in defender's hand. Maximum cards on table count is 5 (hand length - 1) if attack is first
        if len(self.attack_state) == defender.hands_len() - (1 if self.attacks_number == 1 else 0):
            raise ValueError("The maximum number of cards on the table was already reached.")

        throwing_player = self.search_player(throwing_player_id)
        if throwing_player is None: # check if player with given id is actually exist
            raise ValueError("Player with given id not exist")
        if not throwing_player.have_card(card): # validate if user actually have given card in hand
            raise ValueError("Cannot throw a card that is not in player's hand.")

        # according to rules, additional thrown card must have the same rank as one laying on table already (i.e. inside attack_state map)
        contain_same_ranked_card = False
        for b_card, t_card in self.attack_state.items():
            if b_card.get_rank() == card.get_rank() or (t_card is not None and t_card.get_rank() == card.get_rank()): # bottom card can't be None
                contain_same_ranked_card = True
                break

        if not contain_same_ranked_card:
            raise ValueError("Cannot throw an additional card with not valid rank.")

        # throw card on the table
        throwing_player.throw_card(card)
        self.attack_state[card] = None

        self.refill_players_order[throwing_player] = None  # store order to properly refill cards

    def take_cards(self): # defender is taking all cards from the attack. It means that he can't beat one of them (or just want to take)
        defender = self.players[self.get_next_turn()]

        # give all cards from attack to defender's hand
        for b_card, t_card in self.attack_state.items():
            defender.take_card(b_card)
            if t_card is not None:
                defender.take_card(t_card)

        self.attack_state.clear() # clear attack state

    def end_attack(self, defender_picked_up: bool): # should be called when attack is over
        # getting ready to refill hands before self.__turn messes up
        players_to_refill: list[Player] = list[Player](self.refill_players_order.keys()) # get order

        # append defender at the end
        defender = self.players[self.get_next_turn()]
        players_to_refill.append(defender)


        if defender_picked_up: # go to next player if defender picked up the cards
            self.take_cards()
            self.__turn = self.get_next_turn() # move turn 2 timer if defender picked up
        else:
            self.attack_state.clear() # clear attack state

        self.__turn = self.get_next_turn() # change turn to next player

        # refill hands
        for player in players_to_refill:
            while player.hands_len() < 6 and self.deck.cards_available() > 0: # while player have less than 6 cards and some cards left in deck
                player.take_card(self.deck.take_card())

            if player.hands_len() == 0: # Players win if no cards left in hand and deck
                self.winners.append(player)
                self.players.remove(player)

    def search_player(self, player_id: str): # search the player with given id
        for player in self.players:
            if player.get_id() == player_id:
                return player

        return None


    def to_safejson(self, player_id: str): # convert to json excluding sensible fields like every player's hand
        data = {
            "deck": self.deck.to_json(sensible_data=True),
            "players": [p.to_json(player_id) for p in self.players],
            'winners': [p.to_json(player_id) for p in self.winners],
            "attack_state": [[str(bottom_c), str(top_c)] for top_c, bottom_c in self.attack_state.items()],
            "attacks_number": self.attacks_number,
            "turn": self.get_turn(),
            'next_turn': self.get_next_turn(),
            "refill_players_order": [p.to_json() for p in self.refill_players_order.keys()],
        }

        return data

    def to_json(self): # convert table to dictionary to store in database
        data = {
            "deck": self.deck.to_json(),
            "players": [p.to_json() for p in self.players],
            'winners': [p.to_json()  for p in self.winners],
            "attack_state": [[str(bottom_c), str(top_c)] for top_c, bottom_c in self.attack_state.items()],
            "attacks_number": self.attacks_number,
            "turn": self.get_turn(),
            'next_turn': self.get_next_turn(),
            "refill_players_order": [p.to_json() for p in self.refill_players_order.keys()], # keys only, because dict is used as ordered set
        }

        return data

    def __str__(self):
        return str(self.to_json())

    @classmethod
    def from_json(cls, data: (str | dict)): # initialize table with data from database
        if type(data) is str:
            data = json.loads(data)

        players = [Player.from_json(p) for p in data["players"]] # recreate players
        table = cls(players) # construct table

        table.deck = Deck.from_json(data["deck"]) # recreate deck
        table.winners = [Player.from_json(p) for p in data["winners"]] # recreate winners
        table.attack_state = {
            Card.from_string(state[0]): Card.from_string(state[1]) for state in data["attack_state"]
        } # recreate attack state
        table.attacks_number = data["attacks_number"]
        table.__turn = data["turn"]
        table.refill_players_order = {
            Player.from_json(p): None for p in data["refill_players_order"]
        }

        return table



"""
p1 = Player('ASd', 'asd')
p2 = Player('ASasdd', 'asdasd')
t = Table([p1, p2])
t_str = t.to_json()
print(Table.from_str(t_str))
"""

