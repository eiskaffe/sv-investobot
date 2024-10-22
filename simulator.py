from dataclasses import dataclass, field
from enum import Enum
from math import floor, ceil, log
from itertools import chain, combinations
import numpy as np
from alive_progress import alive_bar
import json

# def all_subsets(lst, n):
#     """Generate all subsets of a list of objects with length of the subset at most n."""
#     return list(chain.from_iterable(combinations(lst, r) for r in range(n + 1)))

# def sgn(x: float) -> int:
#     """The mathematical sgn (signum) funcion R->{-1;0;1}"""
#     if x > 0: return 1
#     if x == 0: return 0
#     return -1

# def all_combinations_within_budget(items_with_prices, budget):
#     """
#     Generate all combinations of items with their prices that do not exceed the given budget,
#     allowing multiple instances of the same item and ignoring the order of items in the combinations.
#     """
#     items = list(items_with_prices.items())
#     def find_combinations(remaining_cash, current_combination, start_index):
#         # If the remaining cash is negative, return immediately
#         if remaining_cash < 0:  return
#         # Yield the current combination if the remaining cash is non-negative
#         if remaining_cash >= 0:
#             yield current_combination
#         # Explore further combinations by adding more items
#         for i in range(start_index, len(items)):
#             item, price = items[i]
#             if remaining_cash >= price:
#                 yield from find_combinations(
#                     remaining_cash - price,
#                     current_combination + [(item, price)],
#                     i  # Allow the same item to be added again
#                 )
#     return find_combinations(cash, [], 0)

def monthS(x: int):
    if x == 2: return "spring"
    if x == 3: return "summer"
    if x == 5: return "autumn"
    if x == 7: return "winter"
    raise ValueError("invalid month integer")

def dayS(x: int):
    if not 0 <= x < 7: raise ValueError("invalid weekday")
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x]

MONTH = 28

class Date:
    def __init__(self, epoch: int) -> None:
        if not isinstance(epoch, int): raise TypeError("Date takes int for epoch")
        self.epoch = epoch
        
    def __repr__(self):
        return str(self.epoch)
        
    @property
    def year(self) -> int:
        return ceil(self.epoch/MONTH*4)
    @property
    def monthI(self) -> int:
        """Shifted to the right by one!!!!!"""
        return [4, 1, 2, 3, 4][ceil((self.epoch - MONTH*4*floor(self.epoch/(MONTH*4))) / MONTH)] # look at graph
    @property
    def month(self) -> int:
        return [7, 2, 3, 5, 7][ceil((self.epoch - MONTH*4*floor(self.epoch/(MONTH*4))) / MONTH)] # look at graph
    @property
    def monthS(self):
        return monthS(self.month)
    @property
    def day_of_the_week(self) -> int:
        return self.epoch % 7
    @property
    def day_of_the_weekS(self):
        return dayS(self.day_of_the_week)
    @property
    def day(self) -> int:
        """return is in the interval [1; MONTH]"""
        return MONTH if (t := self.epoch % MONTH) == 0 else t

@dataclass
class Plant:
    growth: int
    regrow: int
    price: int
    sale: int
    _season_: int # 2: spring; 3: summer; 5: autumn; 7: winter (15 summer and autumn (3*5))
    flower: bool # 0: agricultural plant; 1: flower for beekeeping
    season: list = field(init=False)
    
    def __post_init__(self) -> None:
        self.season = [
            self._season_ % 2 == 0,
            self._season_ % 3 == 0,
            self._season_ % 5 == 0,
            self._season_ % 7 == 0
        ]
    
    def profit(self) -> int:
        """Profit"""
        if self.regrow == -1: return self.sale - self.price
        return (floor((MONTH - self.growth - 1) / self.regrow) + 1) * self.sale - self.price
    
    def daily(self) -> float:
        """Daily profit"""
        return self.profit() / (self.growth if self.regrow == -1 else MONTH)

@dataclass
class Asset:
    name: str
    quantity: int
    date: Date # date of planting
    # status: int # -1 seed; 0 planted seed; 1 day1; 2 day2; ... #UNUSED??%?%?
    greenhouse: bool = field(default=False)
    #modifiers?? Greenhouse??
    plant: Plant = field(init=False, repr=False)
    
    def __post_init__(self) -> None:
        if isinstance(self.date, int): self.date = Date(self.date)
        self.plant = PLANTS[self.name]
        for i in range(3):
            if not self.plant.season[(self.date.monthI + i) % 4]: break
        else: self.greenhouse = True
        
    def value(self, today:Date=None) -> int:
        # does it survive the next season?
        
        if not today: raise ValueError("Undated asset")
        
        if not self.greenhouse:     # t = how much until death
            t = MONTH - today.day
            for i in range(3):
                if self.plant.season[(today.monthI + i) % 4]: t += MONTH
                else: break
        elif not self.plant.regrow == -1: return float("inf")        
        
        if self.date.epoch + self.plant.growth > today.epoch + t: return 0              
        if self.plant.regrow == -1: return self.plant.sale*self.quantity
        else:
            # how much harvests left before death?
            return (floor((t - self.plant.growth - self.date.day ) / self.plant.regrow) + 1) * self.plant.sale  # from Plant.profit()
    
    def harvest_day(self, epoch: int) -> int:
        if self.plant.regrow == -1 or self.date.epoch + self.plant.growth >= epoch: 
            return self.date.epoch + self.plant.growth
        elif self.date.epoch + self.plant.growth < epoch:
            return epoch if (k := (epoch - (self.date.epoch + self.plant.growth)) % self.plant.regrow) == 0 \
                    else self.plant.regrow - k + epoch
            
            
            
def assess(assets: list[Asset], d:Date) -> int:
    # print("\nPORTOFOLIO ASSESMENT:")
    s: int = assets[0]
    for asset in assets[1:]:
        # print(asset.name, asset.value(today=d))
        s += asset.value(today=d)
    return s

def simulate(assets:list[Asset], today:Date, T: int = None, different_one_day = 1, elimination_percentile = 50):
    if different_one_day < 0: raise ValueError("different_one_day must be a non-negative integer!")
    
    # weakpoint of the whole operation
    def all_combinations_within_budget(cash):
        """
        Generate all combinations of items with their prices that do not exceed the given budget,
        allowing multiple instances of the same item and ignoring the order of items in the combinations.
        """
        # print(date, date.epoch)
        items = list(PRICES.items())        
        def find_combinations(remaining_cash, current_combination, start_index):
            # Yield the current combination if the remaining cash is non-negative
            if remaining_cash >= 0:
                yield current_combination
            # Explore further combinations by adding more items
            for i in range(start_index, len(items)):
                item, price = items[i]
                if remaining_cash >= price:
                    yield from find_combinations(
                        remaining_cash - price,
                        current_combination + [(item, price)],
                        i  # Allow the same item to be added again
                    )
        
        return find_combinations(cash, [], 0)
    
        
    # Investment ALWAYS pays off -> negative change in porfolio value is a no go.
    # bulk purchases -> light or every combination -> Huge computational demand?!? => different_one_day
    if not T: T = MONTH - today.day
    queue = [(assets, assess(assets, today), [])] # currently, current portf. value, history of purchases list[Asset] 
    for i in range(T):
        print(f"Started simulating day {today.epoch + i} ({i+1}.) with {len(queue)} number of branches")
        
        with alive_bar(len(queue)) as bar:
            tomorrow = []
            while queue:
                a = queue.pop(0)
                for current_combination in all_combinations_within_budget(a[0][0]):
                    # print("new contender")
                # for x in all_combinations_within_budget(a[0][0], Date(today.epoch + i)):
                    cash = 0 + a[0][0]
                    new_assets = list()
                    for n, q in zip(*np.unique([x for x,_ in current_combination], return_counts=True)):
                        cash -= PRICES[n]*q
                        new_assets.append(Asset(n,q,Date(today.epoch + i)))
                    f = a[0] + new_assets
                    # f[0] = cash
                    g = []
                    for asset in f[1:]:
                        if asset.harvest_day(today.epoch + i) <= today.epoch + i:
                            # print(f"selling {asset.name} from day {asset.date.epoch} for {asset.quantity * asset.plant.sale}")
                            cash += asset.quantity * asset.plant.sale
                            # print(f"sold. cash: {cash}")
                        else:
                            # if i > 4: print(f"appending {asset.name} from day {asset.date.epoch}")
                            g.append(asset)
                    
                    g.insert(0, cash)
                    # if not a[1] > (asm := assess(g, Date(today.epoch + i))):
                    tomorrow.append((g, assess(g, Date(today.epoch + i)), a[2] + new_assets))
                    # if i > 4:
                    #     with open(f"TAG_{i+1}.txt", "w+", encoding="utf-8") as outf:
                    #         for k in tomorrow:
                    #             print(k[0], file=outf)
                bar()
        # print(queue)
        
        # print(queue[:3])
        # queue = queue[:100]
        # queue = queue[:ceil(len(queue)*(1-elimination_percentile/100))] # elimination method?!
        
        # static most money
        # tomorrow = list(sorted(tomorrow, key=lambda x:x[1], reverse=True))
        # queue = tomorrow[:min(50, ceil(len(tomorrow)**(1/2)))]
        
        # most profit/history
        tomorrow = list(sorted(tomorrow, key=lambda x:(x[1]/(p if (p := len(x[2])) else 1 )), reverse=True))
        queue += tomorrow[:min(100, ceil(len(tomorrow)**(1/2)))]
        
    # print(queue)
    for i, f in enumerate(queue[:3]):
        print(f"\n|{'='*10}{f'{i+1}. helyezett':^15}{'='*10}|")
        print(f"Összegzett portfólió érték: {f[1]}")
        print(f"{'Nap':<5}{'Név':^12}{'Mennyiség':^10}{'Aratás':>10}")
        with open(f"{i+1}.txt", "w+", encoding="utf-8") as outf:
            for asset in f[0]:
                print(asset, file=outf)
            print("="*10,file=outf)
            for asset in f[2]:
                asset: Asset
                print(f"{asset.date.epoch:<5}{asset.name:^12}{asset.quantity:^10}{(asset.date.epoch+asset.plant.growth):>10}")
                print(asset, file=outf)

    
    
    
def main():
    global PLANTS
    global PRICES
    
    with open("plants.tsv", "r", encoding="utf-8") as inf:
        PLANTS = {
            (k := line.strip().split("\t"))[0]:
            Plant(*map(int,k[1:]))
            for line in inf
        }
    with open("start.tsv", "r", encoding="utf-8") as inf:
        ASSETS = [int(inf.readline().strip())]
        ASSETS[1:] = [
            Asset((k := line.strip().split("\t"))[0], *map(int,k[1:]))
            for line in inf
        ]
    
    print(PLANTS)
    print()
    # print(MONEY)
    print(ASSETS)
    PLANTS = {i:p for i,p in PLANTS.items() if not p.flower}
    PRICES = {name:plant.price for name, plant in PLANTS.items()}


    for name, plant in PLANTS.items():
        print(name, plant.profit(), plant.daily())
        
    print(assess(ASSETS, Date(1)))
    
    simulate(ASSETS, Date(1), 21)
    

if __name__ == "__main__":
    main()