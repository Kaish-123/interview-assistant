#!/bin/python3

import os

def changeAds(base10):
    """
    Convert base10 to binary, remove leading zeros, flip all bits starting
    from the highest-order 1 bit, and convert back to base10.
    
    Algorithm:
    1. Convert base10 to binary
    2. Remove leading zeros
    3. Flip all bits from the highest-order 1 bit (which means flip all remaining bits)
    4. Convert back to base10
    """
    # Handle edge case: if base10 is 0, return 0
    if base10 == 0:
        return 0
    
    # Step 1: Convert to binary and remove leading zeros
    binary_str = bin(base10)[2:]  # bin() returns '0b...', so we skip '0b'
    
    # Step 2: Binary string already has no leading zeros after bin()[2:]
    # Step 3: Flip all bits (starting from highest-order 1 means flipping all bits)
    flipped_binary = ''.join('1' if bit == '0' else '0' for bit in binary_str)
    
    # Step 4: Convert back to base10
    result = int(flipped_binary, 2)
    
    return result


if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')
    
    base10 = int(input().strip())
    
    result = changeAds(base10)
    
    fptr.write(str(result) + '\n')
    
    fptr.close()
