import numpy as np
import random

TOP_FS = 'aa0003'
MIDDLE_FS = 'aa0004'
BOTTOM_FS = 'aa0005'

COLORS = ['green','blue','yellow','red']

CURSED_LANDS = ['aa000_','aa0001','aa0002']
BASE_FERTS = ['af0003','af0004','af0005']

FERT_SOIL = [TOP_FS,MIDDLE_FS,BOTTOM_FS]
HIGHEST_ADV_ONES = 63
EXCLUDED_ONES = ['aa0022']
HIGHEST_ADV_TWOS = 50
EXCLUDED_TWOS = ['ab0007','ab0042','ab0049']
HIGHEST_ADV_THREES = 43
EXCLUDED_THREES = []
NUM_VALE_ONES = 28
NUM_VALE_TWOS = 26
NUM_LEADERS = 8

ADV_ONES = ['aa' + str(i).rjust(4,'0') for i in range(6, HIGHEST_ADV_ONES+1)] # format: aa____
[ADV_ONES.remove(one) for one in EXCLUDED_ONES]
ADV_TWOS = ['ab' + str(i).rjust(4,'0') for i in range(HIGHEST_ADV_TWOS+1)] # ab____
[ADV_TWOS.remove(two) for two in EXCLUDED_TWOS]
ADV_THREES = ['ac' + str(i).rjust(4,'0') for i in range(HIGHEST_ADV_THREES+1)] # ac____
[ADV_THREES.remove(three) for three in EXCLUDED_THREES]
VALE_ONES = ['va' + str(i).rjust(4,'0') for i in range(NUM_VALE_ONES)] # va____
VALE_TWOS = ['vb' + str(i).rjust(4,'0') for i in range(NUM_VALE_TWOS)] # vb____
LEADERS = ['al' + str(i).rjust(3,'0') + 'a' for i in range(NUM_LEADERS)] # format: al___a

class Card:
    def __init__(self,id,advancement=None):
        self.advancements = dict()
        self.id = id
        if advancement:
            self.advancements[advancement] = advancement

    def add(self,advancement):
        self.advancements[advancement] = advancement

    def dictify(self):
        return {'advancements':list(self.advancements.keys()),'id':self.id}

    def listify_advs(self):
        return list(self.advancements.keys())


class Player:
    def __init__(self,name,id):
        self.name = name
        self.id = id
        self.color = None

        self.deck = []
        self.discard = []
        self.vales = dict()
        self.points = 0
        self.field = dict()
        self.new_game()
        self.token = False
        self.on_deck = None
        self.is_first = False
        self.leader = None

    def new_game(self):
        self.deck = [Card('c' + str(i)) for i in range(8)] + \
                    [Card('c' + str(i+8),CURSED_LANDS[0]+str(i)) for i in range(3)] + \
                    [Card('c' + str(i+11),CURSED_LANDS[1]+str(i)) for i in range(3)] + \
                    [Card('c' + str(i+14),CURSED_LANDS[2]+str(i)) for i in range(3)] + \
                    [Card('c17',BASE_FERTS[0]),Card('c18',BASE_FERTS[1]),Card('c19',BASE_FERTS[2])]
        random.shuffle(self.deck)
        self.discard = []
        self.vales = dict()
        self.field = dict()
        self.on_deck = self.deck.pop()
        self.points = 0
        self.token = False
        self.leader = None
        if not self.color:
            self.color = random.choice(COLORS)
        self.is_first = False

    def play_on_deck(self):
        # if no on deck card (via html glitch), do nothing
        if not self.on_deck:
            return None

        # add card to field
        self.field[self.on_deck.id] = self.on_deck
        self.on_deck = None
        if self.deck:
            return {'color':self.color, 'remaining':len(self.deck)}
        else:
            return {'color':None, 'remaining':len(self.deck)}

    def flip(self):
        # if no cards left, can't draw
        if not self.discard and not self.deck:
            return None

        # if dont already have on deck card (no glitch in html), draw
        if not self.on_deck:
            if not self.deck:
                self.deck = self.discard
                random.shuffle(self.deck)
                self.discard = []
            self.on_deck = self.deck.pop()
        return {'card':self.on_deck.dictify(), 'remaining':len(self.deck)}

    def shuffle(self):
        if self.on_deck:
            self.deck.append(self.on_deck)
        self.on_deck = None
        random.shuffle(self.deck)
        return self.color

    def make_on_deck(self,card):
        if self.on_deck:
            self.deck.append(self.on_deck)
        self.on_deck = card

    def make_deck_bottom(self,card):
        self.deck.insert(0,card)

    def flip_token(self):
        self.token = not self.token

    def add_vale(self,vale):
        self.vales[vale] = vale

    def add_advancement(self,card,advancement):
        self.field[card].add(advancement)

    def discard_field(self):
        self.discard.extend(list(self.field.values()))
        self.field = dict()

    def deck_cards(self):
        return [card.id for card in self.deck]

    def discard_cards(self):
        return [card.id for card in self.deck]

    def discard_card(self,card):
        if isinstance(card,Card):
            self.discard.append(card)
        elif card in self.field:
            self.discard.append(self.field.pop(card))
        elif card in self.deck_cards():
            self.discard.append(self.deck.pop(self.deck_cards().index(card)))
        else:
            raise Exception('Invalid discard attempt')

    def discard_vale(self,vale):
        del self.vales[vale]

    def score_points(self,points):
        self.points += points

    def set_color(self,color):
        self.color = color

    def set_leader(self,leader):
        self.shuffle()
        self.deck[self.deck_cards().index('c0')].add(leader)
        self.leader = leader
        self.flip()

    def flip_leader(self):
        del self.field['c0'].advancements[self.leader]
        self.leader = self.leader[0:5] + ('b' if self.leader[5] == 'a' else 'a')
        self.field['c0'].advancements[self.leader] = self.leader
        return self.leader

class Game:
    def __init__(self):
        self.players = dict()
        self.next_id = 1
        self.players_turn = 0
        self.in_progress = False
        self.turn_status = None
        self.using_leaders = False

        self.adv_ones = []
        self.adv_twos = []
        self.adv_threes = []
        self.vale_ones = []
        self.vale_twos = []
        self.leaders = []
        self.fertile_soils = {TOP_FS:6,MIDDLE_FS:6,BOTTOM_FS:6}

        self.purgatory = {'cards':dict(),'others':dict()}
        self.points_left = 0

    def add_player(self,name):
        # add player to game
        id = self.next_id
        self.players[id] = Player(name,id)
        self.next_id += 1
        return id

    def new_game(self):
        # shuffle piles
        np.random.seed()
        l1_qty = 6+3*len(self.players) # number of level one cards
        self.points_left = 13+5*len(self.players) # number of points
        self.adv_ones = list(np.random.permutation(ADV_ONES))[0:l1_qty]
        self.adv_twos = list(np.random.permutation(ADV_TWOS))
        self.adv_threes = list(np.random.permutation(ADV_THREES))
        self.vale_ones = list(np.random.permutation(VALE_ONES))
        self.vale_twos = list(np.random.permutation(VALE_TWOS))
        self.leaders = list(np.random.permutation(LEADERS))
        self.fertile_soils = {TOP_FS: 6, MIDDLE_FS: 6, BOTTOM_FS: 6}

        self.purgatory = {'cards': dict(), 'others': dict()}

        for player in self.players.values():
            player.new_game()

        self.players_turn = random.choice(list(self.players.keys()))
        self.players[self.players_turn].is_first = True
        self.in_progress = True
        self.turn_status = [self.players_turn,0]

    # move items places
    def move(self,item,source,destination,player,source_card=None):
        return_value = (None, item)
        self.turn_status[1] += 1

        # buying advancement
        if source == 'adv_deck' and destination[0] == 'c':
            return self.add_advancement(player,destination,item)

        # otherwise, determine source of card
        if source == 'purgatory':
            if item[0] == 'c':
                source = self.purgatory['cards']
            else:
                source = self.purgatory['others']
        elif source == 'field':
            if source_card:
                source = self.players[player].field[source_card].advancements
            else:
                source = self.players[player].field
        elif source == 'vales':
            source = self.players[player].vales
        elif source == 'deck':
            source = self.players[player].deck
        elif source == 'discard':
            source = self.players[player].discard
        else:
            raise Exception('Invalid Source')

        # determine destination of card
        # moving to deck, discarding, and moving from deck or discard to purgatory is special case
        if destination == 'deck':
            item = source.pop(item) if isinstance(source,dict) else source.pop([card.id for card in source].index(item))
            self.players[player].make_on_deck(item)
            return
        if destination == 'deck_bottom':
            item = source.pop(item) if isinstance(source,dict) else source.pop([card.id for card in source].index(item))
            self.players[player].make_deck_bottom(item)
            return
        if destination == 'discard':
            if item in self.purgatory['cards']:
                self.players[player].discard_card(self.purgatory['cards'].pop(item))
            else:
                self.players[player].discard_card(item)
            return
        if destination == 'purgatory':
            if item[0] == 'c':
                destination = self.purgatory['cards']
            else:
                destination = self.purgatory['others']
        elif destination == 'field':
            destination = self.players[player].field
        elif destination in self.players[player].field:
            destination = self.players[player].field[destination].advancements
        elif destination == 'vales':
            destination = self.players[player].vales
        else:
            raise Exception('Invalid Destination')

        if isinstance(source,dict):
            destination[item] = source.pop(item)
        elif isinstance(source[0],Card):
            destination[item] = source.pop([card.id for card in source].index(item))
        else:
            destination[item] = item
            source.remove(item)

        # return next advancement, if necessary
        return return_value

    def add_points(self,points):
        self.points_left += int(points)
        return self.points_left

    def get_state(self,id):
        pt = self.players[self.players_turn]
        return {'adv_ones':self.adv_ones[0:min(3,len(self.adv_ones))],
                'adv_twos':self.adv_twos[0:min(3,len(self.adv_twos))],
                'adv_threes': self.adv_threes[0:min(3, len(self.adv_threes))],
                'vale_ones':self.vale_ones[0:min(4, len(self.vale_ones))],
                'vale_twos':self.vale_twos[0:min(4, len(self.vale_twos))],
                'score':self.players[id].points,
                'field':self.players[id].field,
                'on_deck':self.players[id].on_deck,
                'vales':self.players[id].vales,
                'purgatory':self.purgatory,
                'fertile_soils':self.fertile_soils,
                'points_left':self.points_left,
                'discard':self.players[id].discard,
                'deck_left':len(self.players[id].deck),
                'color':self.players[id].color,
                'flipped':self.players[id].token,
                'is_first':self.players[id].is_first,
                'deck':self.players[id].deck,
                'random_deck':list(np.random.permutation(self.players[id].deck)),
                'adv_ones_left':len(self.adv_ones) - 3,
                'using_leaders':self.using_leaders,
                'players_turn':None if pt.id == id else {'name':pt.name, 'field':pt.field, 'on_deck':pt.on_deck, 'vales':pt.vales,
                                   'deck_left':len(pt.deck),'color':pt.color,'flipped':pt.token,
                                   'is_first':pt.is_first,'id':pt.id, 'score':pt.points},
                'other_players': [{'name':player.name, 'field':player.field, 'on_deck':player.on_deck, 'vales':player.vales,
                                   'deck_left':len(player.deck),'color':player.color,'flipped':player.token,
                                   'is_first':player.is_first, 'score':player.points}
                                  for player in self.players.values() if player.id != id and player.id != self.players_turn]}

    def get_players(self):
        return [player.name for player in self.players.values()]

    def add_advancement(self,player,card,advancement):
        self.turn_status[1] += 1

        # initiate return value
        remainder = None

        # remove advancement from deck
        if advancement in FERT_SOIL:
            self.fertile_soils[advancement] -= 1
            remainder = self.fertile_soils[advancement]
            advancement = advancement + str(self.fertile_soils[advancement])
        elif advancement[1] == 'a' or advancement in self.adv_ones:
            self.adv_ones.remove(advancement)
            if len(self.adv_ones) < 3:
                self.adv_ones.append(self.adv_twos.pop(3))
        elif advancement[1] == 'b':
            self.adv_twos.remove(advancement)
        else:
            self.adv_threes.remove(advancement)

        # add advancement to card
        self.players[player].add_advancement(card,advancement)

        # return next card (or size of fertile soil piles)
        return remainder, advancement

    def add_vale(self, player, vale):
        self.turn_status[1] += 1

        # give vale card to player
        self.players[player].add_vale(vale)

        # remove vale from deck
        if vale[1] == 'a':
            self.vale_ones.remove(vale)
            return self.vale_ones[3]
        else:
            self.vale_twos.remove(vale)
            return self.vale_twos[3]

    def end_turn(self,player):
        # discard field
        self.players[player].discard_field()

        if self.players_turn != player:
            return

        # update whose turn
        idx = (list(self.players.keys()).index(self.players_turn) + 1) % len(self.players)
        self.players_turn = list(self.players.keys())[idx]
        self.turn_status = [self.players_turn, 0]

    def end_game(self):
        self.players = dict()
        self.in_progress = False

    def play_on_deck(self,player):
        self.turn_status[1] += 1
        return self.players[player].play_on_deck()

    def flip(self,player):
        self.turn_status[1] += 1
        return self.players[player].flip()

    def flip_token(self, player):
        self.turn_status[1] += 1
        self.players[player].flip_token()
        return True

    def score_points(self,player,points):
        self.turn_status[1] += 1
        self.players[player].score_points(points)
        self.add_points(-points)
        return self.players[player].points, self.points_left

    def set_color(self,player,color):
        self.players[player].set_color(color)

    def discard_vale(self,player,vale,source):
        self.turn_status[1] += 1
        if source == 'vales':
            self.players[player].discard_vale(vale)
        else:
            del self.purgatory['others'][vale]

    def shuffle(self,player):
        self.turn_status[1] += 1
        return self.players[player].shuffle()

    def get_turn_status(self):
        return self.turn_status

    def set_leaders(self,using_leaders):
        self.using_leaders = using_leaders == 'true'

    def set_leader(self,id,leader):
        return self.players[id].set_leader(leader)

    def flip_leader(self, id):
        self.turn_status[1] += 1
        return self.players[id].flip_leader()

    def leader_options(self,id):
        leaders = self.leaders[list(self.players.keys()).index(id)*2:list(self.players.keys()).index(id)*2+2]
        return leaders, list(map(lambda l: l[0:5] + 'b',leaders))

    def needs_leader(self,id):
        return self.using_leaders and not self.players[id].leader

    def discard_field(self,id):
        return self.players[id].discard_field()