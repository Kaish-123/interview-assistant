import java.util.*;

/**
 * Minimum operations to turn source into target using:
 * - add 1 to prefix [0..i]
 * - add 1 to suffix [i..n-1]
 * Each use counts as one operation. Only increments; impossible if any target[i] &lt; source[i].
 *
 * Let d[i] = target[i] - source[i]. Minimum ops = d[n-1] + sum_{k=0}^{n-2} max(0, d[k]-d[k+1])
 * iff all d[i] &gt;= 0 and d[0] &gt;= sum_{k=0}^{n-2} max(0, d[k]-d[k+1]); else -1.
 */
public class GetMinOperations {

    public static long getMinOperations(long[] source, long[] target) {
        int n = source.length;
        if (n != target.length) {
            return -1;
        }
        if (n == 0) {
            return 0;
        }

        long[] d = new long[n];
        for (int i = 0; i < n; i++) {
            d[i] = target[i] - source[i];
            if (d[i] < 0) {
                return -1;
            }
        }

        long needFromDrops = 0;
        for (int k = 0; k < n - 1; k++) {
            if (d[k] > d[k + 1]) {
                needFromDrops += d[k] - d[k + 1];
            }
        }

        if (d[0] < needFromDrops) {
            return -1;
        }

        return d[n - 1] + needFromDrops;
    }

    // Alias for platforms that use this name
    public static long getMinimumOperations(long[] source, long[] target) {
        return getMinOperations(source, target);
    }

    public static void main(String[] args) {
        assertEq(2L, getMinOperations(arr(1, 2, 2), arr(2, 2, 3)));
        assertEq(6L, getMinOperations(arr(1, 2, 3, -1, 0), arr(3, 4, 3, 0, 4)));
        assertEq(-1L, getMinOperations(arr(1, 2, 3, 0), arr(1, 3, 3, 0)));
        assertEq(0L, getMinOperations(arr(5), arr(5)));
        assertEq(10L, getMinOperations(arr(0), arr(10)));
        System.out.println("All tests passed.");
    }

    private static long[] arr(long... a) {
        return a;
    }

    private static void assertEq(long expected, long actual) {
        if (expected != actual) {
            throw new AssertionError("expected " + expected + " got " + actual);
        }
    }
}
