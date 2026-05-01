import math
import os
import random
import re
import sys


def reverse_string(s):
    return s[::-1]


if __name__ == "__main__":
    fptr = open(os.environ["OUTPUT_PATH"], "w")

    s_count = int(input().strip())

    s = []

    for _ in range(s_count):
        s_item = input()
        s.append(s_item)

    result = reverse_string(s)

    fptr.write("\n".join(result))
    fptr.write("\n")

    fptr.close()
