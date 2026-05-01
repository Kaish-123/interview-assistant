import java.io.*;
import java.util.*;

public class Solution {

    /**
     * Class President (Josephus): n students in a circle 1..n, start at 1,
     * count k students (including the starting student), remove that student,
     * repeat from the next student until one remains.
     */
    public static int whoIsElected(int n, int k) {
        int survivor0 = 0; // 0-based index of survivor among n people
        for (int i = 2; i <= n; i++) {
            survivor0 = (survivor0 + k) % i;
        }
        return survivor0 + 1;
    }

    public static boolean doTestsPass() {
        int[][] testCases = {
            {1, 1, 1},
            {2, 2, 1},
            {4, 2, 1},
            {100, 2, 73},
        };

        for (int[] testCase : testCases) {
            int answer = whoIsElected(testCase[0], testCase[1]);
            if (answer != testCase[2]) {
                System.out.printf(
                    "test failed! n:%d, k:%d, expected:%d, actual:%d%n",
                    testCase[0], testCase[1], testCase[2], answer);
                return false;
            }
        }
        System.out.println("All tests passed");
        return true;
    }

    public static void main(String[] args) {
        doTestsPass();
    }
}
