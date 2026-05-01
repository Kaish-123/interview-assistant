import java.util.HashMap;
import java.util.Map;

public class Solution {
  /**
   * countLengthOfCycle(arr, startIndex)
   *
   * You are given an integer array of size N.
   * Every element of the array is greater than or equal to 0.
   * Starting from arr[startIndex], follow each element to the index it points to.
   * Continue to do this until you find a cycle.
   *
   * Return the length of the cycle. If no cycle is found return -1.
   *
   * Examples:
   * countLengthOfCycle([1, 0], 0) == 2
   * countLengthOfCycle([1, 2, 0], 0) == 3
   */
  public static int countLengthOfCycle(int[] arr, int startIndex) {
    if (arr == null || arr.length == 0) {
      return -1;
    }
    if (startIndex < 0 || startIndex >= arr.length) {
      return -1;
    }

    // Map index -> step when first visited.
    Map<Integer, Integer> firstSeenAtStep = new HashMap<>();

    int idx = startIndex;
    int step = 0;
    while (true) {
      if (idx < 0 || idx >= arr.length) {
        return -1; // walked off the array => no cycle
      }

      Integer firstSeen = firstSeenAtStep.get(idx);
      if (firstSeen != null) {
        return step - firstSeen; // current idx repeats => cycle length
      }

      firstSeenAtStep.put(idx, step);
      step++;
      idx = arr[idx];
    }
  }

  /**
   * boolean doTestsPass()
   * Returns true if all the tests pass. Otherwise returns false.
   */
  public static boolean doTestsPass() {
    boolean testsPassed = true;

    testsPassed &= countLengthOfCycle(new int[] {1, 0}, 0) == 2;
    testsPassed &= countLengthOfCycle(new int[] {1, 2, 0}, 0) == 3;

    // Additional tests
    testsPassed &= countLengthOfCycle(new int[] {0}, 0) == 1; // self-loop
    testsPassed &= countLengthOfCycle(new int[] {2, 2, 2}, 0) == 1; // enters 2->2
    testsPassed &= countLengthOfCycle(new int[] {1, 2, 3}, 0) == -1; // off the end
    testsPassed &= countLengthOfCycle(new int[] {1, 2, 3}, 2) == -1; // start near end
    testsPassed &= countLengthOfCycle(new int[] {1, 0}, -1) == -1; // invalid start
    testsPassed &= countLengthOfCycle(new int[] {1, 0}, 2) == -1; // invalid start

    if (testsPassed) {
      System.out.println("Test passed.");
      return true;
    } else {
      System.out.println("Test failed.");
      return false;
    }
  }

  public static void main(String[] args) {
    doTestsPass();
  }
}

