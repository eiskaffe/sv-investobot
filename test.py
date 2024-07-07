A = [1,2,3,4,5]
print(A[:len(A)-1])

for i in range(10, 10):
    print(i)
    
from itertools import chain, combinations
import pandas as pd
import numpy as np

def all_subsets(lst, n):
    """Generate all subsets of a list of objects with length of the subset at most n."""
    return list(chain.from_iterable(combinations(lst, r) for r in range(n + 1)))

def all_combinations_within_budget(items_with_prices, cash):
    """
    Generate all combinations of items with their prices that do not exceed the given budget,
    allowing multiple instances of the same item and ignoring the order of items in the combinations.
    
    :param items_with_prices: Dictionary with items as keys and their prices as values
    :param cash: Maximum budget
    :return: Generator of all unique combinations of items within the given budget
    """
    items = list(items_with_prices.items())
    
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

# Example usage
items_with_prices = {'item1': 10, 'item2': 20, 'item3': 5}
cash = 20
# combinations_within_budget = 

# Print the combinations
# for combination in all_combinations_within_budget(items_with_prices, cash):
    # print(combination)
    # ...


A = [('Parsnip', 20), ('Parsnip', 20), ('Parsnip', 20), ('Parsnip', 20), ('Potato', 50), ('Potato', 50), ('Potato', 50), ('Potato', 50), ('Potato', 50), ('Tulip', 20), ('Tulip', 20), ('Tulip', 20), 
('Tulip', 20), ('Jazz', 30), ('Bean', 60)]
# print(zip(*np.unique([x for x,_ in A], return_counts=True)))
for a,b in zip(*np.unique([x for x,_ in A], return_counts=True)):
    print(a, b)




# # Example usage
# lst = ['a', 'b', 'c']
# n = 2
# subsets = all_subsets(lst, n)
# print(subsets)
