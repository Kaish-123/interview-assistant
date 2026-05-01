import java.util.HashMap;
import java.util.Map;

public class Solution {

  /**
   * For each student, average = floor(sum of scores / count). Return the maximum
   * such average. Empty input returns 0.
   *
   * <p>Integer division is not the same as floor for negative averages (e.g. -1/2
   * truncates to 0 in Java; floor(-0.5) is -1), so we use {@link Math#floor}.
   */
  public static int bestAverageGrade(String[][] scores) {
    if (scores == null || scores.length == 0) {
      return 0;
    }

    Map<String, long[]> sumAndCount = new HashMap<>();
    for (String[] row : scores) {
      if (row == null || row.length < 2) {
        continue;
      }
      String name = row[0];
      int value = Integer.parseInt(row[1]);
      sumAndCount.merge(name, new long[] {value, 1L}, (a, b) -> {
        a[0] += b[0];
        a[1] += b[1];
        return a;
      });
    }

    if (sumAndCount.isEmpty()) {
      return 0;
    }

    int best = Integer.MIN_VALUE;
    for (long[] agg : sumAndCount.values()) {
      long sum = agg[0];
      long count = agg[1];
      int avg = (int) Math.floor((double) sum / (double) count);
      if (avg > best) {
        best = avg;
      }
    }
    return best;
  }

  public static boolean doTestsPass() {
    boolean ok = true;

    String[][] tc1 = {
      {"Bobby", "87"},
      {"Charles", "100"},
      {"Eric", "64"},
      {"Charles", "22"}
    };
    ok &= bestAverageGrade(tc1) == 87;

    ok &= bestAverageGrade(new String[0][0]) == 0;
    ok &= bestAverageGrade(null) == 0;

    // Bobby 75 floor, Charles 100
    String[][] tc2 = {
      {"Bobby", "87"},
      {"Charles", "100"},
      {"Bobby", "64"}
    };
    ok &= bestAverageGrade(tc2) == 100;

    // All-negative bests: must not default to 0
    String[][] tcNeg = {{"A", "-10"}, {"B", "-3"}};
    ok &= bestAverageGrade(tcNeg) == -3;

    // Floor on negative average: (-1 + 0) / 2 = -0.5 -> -1
    String[][] tcFloorNeg = {{"X", "0"}, {"X", "-1"}};
    ok &= bestAverageGrade(tcFloorNeg) == -1;

    // Large sums stay in long (no int overflow in total)
    String[][] tcBig = {{"P", "2000000000"}, {"P", "2000000000"}};
    ok &= bestAverageGrade(tcBig) == 2000000000;

    return ok;
  }

  public static void main(String[] args) {
    if (doTestsPass()) {
      System.out.println("All tests pass");
    } else {
      System.out.println("Tests fail.");
    }
  }
}
