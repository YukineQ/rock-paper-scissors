import sys
import secrets
import hmac
import hashlib
import random
from typing import List
from rich.table import Table
from rich.console import Console


class MenuItemError(Exception):
    def __init__(self, message = 'No such number in menu') -> None:
        super().__init__(message)
    

class MovesArray:    
    def __get__(self, obj, type=None):
        return self.list
    
    def __set__(self, obj, list):
        if len(list) < 3:
            raise ValueError('Moves list must be longer or equals 3')
        if len(list) % 2 != 1:
            raise ValueError('Moves list must be odd')
        if len(list) != len(set(list)):
            raise ValueError('All values must me unique')
        self.list = list
        
        
class RandomKey:
    def generateRandomKey(self):
        return secrets.token_hex(32).encode()
        

class HMAC_SHA256:
    def __init__(self, secretKey):
        self.secretKey = secretKey
        
    def generateHMACForMove(self, move):
        return hmac.new(self.secretKey, str(move).encode(), hashlib.sha256).hexdigest()
        

class Rules:
    def __init__(self, possibleMoves: List):
        self.possibleMoves = possibleMoves
        
    def getWinningChoice(self, moves):
        for move in moves:
            for _ in moves:
                if move == _:
                    continue
                if not self.getDuelWinner(move, _):
                    break
                return move
                
    def getDuelWinner(self, move1, move2):
        firstMoveIndex = self.__getMoveIndex(move1)
        secondMoveIndex = self.__getMoveIndex(move2)
        
        if firstMoveIndex - secondMoveIndex >= (len(self.possibleMoves) - 1)/2 \
            or firstMoveIndex > secondMoveIndex:
            return True
        
        return False
    
    def __getMoveIndex(self, move):
        return self.possibleMoves.index(move)
                    

class HelpTable:    
    def __init__(self, availableMoves):
        self.availableMoves = availableMoves
    
    def printTable(self):
        table = Table(title="Who wins who")
        
        rules = Rules(self.availableMoves)
   
        temp = {
            False: 'Lose',
            True: 'Win'
        }
        
        rows = [[
            temp[rules.getDuelWinner(row, elem)] 
            if row != elem else 'Draw' 
            for elem in self.availableMoves] 
                for row in self.availableMoves
        ]
                
        columns = self.availableMoves
        
        table.add_column('')
        for column in columns:
            table.add_column(column)
            
        for index, row in enumerate(rows):
            _ = [self.availableMoves[index]] + row
            table.add_row(*_)
        
        Console().print(table)


class Item:
    def __init__(self, name, action = None, params=None):
        self.name = name
        self.action = action
        self.params = params
        
    def getName(self):
        return self.name
        
    def execute(self):
        if not self.action:
            return
        
        if not self.params:
            self.action()
            return
        self.action(self.params)
            

class Menu:
    def __init__(self):
        self.items = {}
        
    def add_item(self, number, item: Item):
        self.items[str(number)] = item
        
    def display(self):
        print('Menu:')
        for number, item in self.items.items():
            print(f'{number} - {item.getName()}')
            
    def select_item(self, number):
        item = self.items.get(number)
        if not item:
            raise MenuItemError()        
        item.execute()


class Player:
    def __init__(self, name):
        self.name = name
        self.choice = None
        
    def choose(self, choice):
        self.choice = choice
        
    def getChoice(self):
        return self.choice
    
    def getChoiceTitle(self):
        print(f'{self.name} select {self.choice}')
        
        
class Computer(Player):
    def __init__(self, getHMAC):
        self.getHMAC = getHMAC
        super().__init__('Computer')
        
    def choose(self, possibleMoves):
        self.choice = random.choice(possibleMoves)
        print(f'HMAC: {self.getHMAC(self.choice)}')
        

class Game:
    possibleMoves = MovesArray()
    
    def __init__(self, possibleMoves, players: List[Player], rules=Rules, menu=Menu()):
        self.possibleMoves = possibleMoves
        self.players = players
        self.rules = rules(possibleMoves)
        self.menu = menu
    
    def playGame(self):
        all_choices_selected = False
        
        while not all_choices_selected:
            all_choices_selected = True
            for player in self.players:        
                if player.getChoice() is not None:
                    continue
                
                if player.getChoice() is None:
                    all_choices_selected = False
                        
                if isinstance(player, Computer):
                    player.choose(self.possibleMoves)
                else:
                    for index, move in enumerate(self.possibleMoves):
                        self.menu.add_item(index + 1, Item(move, player.choose, move))
                    self.menu.display()
                    self.menu.select_item(input(f'{player.name}, select ur move: '))         
    
        playersChoices = {player.getChoice() for player in self.players}
        winningMove = self.rules.getWinningChoice(playersChoices)
        winners = [player.name for player in self.players if player.getChoice() == winningMove]
        
        for player in self.players:
            player.getChoiceTitle()
            
        if not winners:
            print('Draw')
        else:
            print(f'{list_to_string(winners)} wins')
            
def list_to_string(list):
    return ", ".join(list)
        

def main():
    try:
        availableMoves = sys.argv[1:]
        
        helpTable = HelpTable(availableMoves)
        menu = Menu()
        
        menu.add_item(0, Item('exit', sys.exit))
        menu.add_item('?', Item('help', helpTable.printTable))
        
        randomKey = RandomKey().generateRandomKey()
        hmacGenerator = HMAC_SHA256(randomKey).generateHMACForMove
        
        game = Game(
            availableMoves, 
            [Computer(hmacGenerator), Player('Player #1'),], 
            menu=menu
        )
        game.playGame()
        
        print(f'HMAC key: {randomKey.decode()}')
    except Exception as e:
        Console().print(e)
        

if __name__ == '__main__':
    main()