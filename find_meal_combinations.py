import os
from itertools import combinations

def findMealCombinations(menu, budget):
    """
    Find all possible meal pairs that can be ordered within the given budget.
    
    Args:
        menu: List of tuples, where each tuple is (id, name, price)
              id and price are strings, name is a string
        budget: Integer representing the maximum budget
    
    Returns:
        List of lists, where each inner list contains two item IDs (as strings)
        representing a valid meal pair within the budget
    """
    result = []
    
    # Generate all pairs of menu items
    for i in range(len(menu)):
        for j in range(i + 1, len(menu)):
            item1 = menu[i]
            item2 = menu[j]
            
            # Extract IDs and prices
            id1, _, price1_str = item1
            id2, _, price2_str = item2
            
            # Convert prices from strings to integers
            price1 = int(price1_str)
            price2 = int(price2_str)
            
            # Check if the pair is within budget
            if price1 + price2 <= budget:
                result.append([id1, id2])
    
    return result


if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')
    
    menu_rows = int(input().strip())
    menu_columns = int(input().strip())
    
    menu = []
    
    for _ in range(menu_rows):
        menu.append(input().rstrip().split(','))
    
    budget = int(input().strip())
    
    result = findMealCombinations(menu, budget)
    
    fptr.write('\n'.join([' '.join(map(str, x)) for x in result]))
    fptr.write('\n')
    
    fptr.close()
