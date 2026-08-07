# Implement the function that returns second smallest element
# Returns None if there is no second smallest
# Eg: secondSmallest([]) -> None
# Eg: secondSmallest([1]) -> None
# Eg: secondSmallest([1, 1]) -> 1
# Eg: secondSmallest([1, 2]) -> 2
# Eg: secondSmallest([1, 1, 2]) -> 1
# Eg: secondSmallest([-1,0,1,-2,2]) -> -1
# Eg: secondSmallest([1,0,1,-1,-1,0]) -> -1

def secondSmallest(x):
  if len(x) < 2:
    return None
  first = second = float('inf')
  for number in x:
    if number < first:
      second = first
      first = number
    elif number < second:
      second = number
  return None if second == float('inf') else second

def doTestsPass():
  """ Returns True if all tests pass. Otherwise returns False """
  testArrays = [[], [0], [0, 1], [-1, 0, 1, -2, 2], [1, 1, 2]]
  testAnswers = [None, None, 1, -1, 1]

  for i in range(len(testArrays)):
    if not (secondSmallest(testArrays[i]) == testAnswers[i]):
      return False
  return True

if __name__ == "__main__":
  if doTestsPass():
    print("All tests pass")
  else:
    print("Not all tests pass")
