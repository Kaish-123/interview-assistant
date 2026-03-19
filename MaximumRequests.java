import java.io.*;
import java.util.*;
import java.util.stream.*;

class Result {
    /*
     * Complete the 'maximumRequests' function below.
     *
     * The function is expected to return an INTEGER.
     * The function accepts following parameters:
     *  1. INTEGER window
     *  2. INTEGER_ARRAY timestamps (sorted non-decreasing)
     *
     * Find the maximum number of requests within any time window [x, x + window - 1].
     */
    public static int maximumRequests(int window, List<Integer> timestamps) {
        if (timestamps == null || timestamps.isEmpty()) {
            return 0;
        }

        int n = timestamps.size();
        int maxCount = 1;
        int left = 0;

        // Sliding window: for timestamps to fit in [x, x+window-1], we need
        // timestamps[right] - timestamps[left] <= window - 1
        for (int right = 0; right < n; right++) {
            while (timestamps.get(right) - timestamps.get(left) > window - 1) {
                left++;
            }
            maxCount = Math.max(maxCount, right - left + 1);
        }

        return maxCount;
    }
}

public class Solution {
    public static void main(String[] args) throws IOException {
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(System.in));
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(System.getenv("OUTPUT_PATH")));

        int window = Integer.parseInt(bufferedReader.readLine().trim());
        int timestampsCount = Integer.parseInt(bufferedReader.readLine().trim());

        List<Integer> timestamps = IntStream.range(0, timestampsCount)
            .mapToObj(i -> {
                try {
                    return bufferedReader.readLine().replaceAll("\\s+$", "");
                } catch (IOException ex) {
                    throw new RuntimeException(ex);
                }
            })
            .map(String::trim)
            .map(Integer::parseInt)
            .collect(Collectors.toList());

        int result = Result.maximumRequests(window, timestamps);

        bufferedWriter.write(String.valueOf(result));
        bufferedWriter.newLine();

        bufferedReader.close();
        bufferedWriter.close();
    }
}
