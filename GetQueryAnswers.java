import java.io.*;
import java.util.*;
import java.util.stream.*;

class Result {
    /*
     * Complete the 'getQueryAnswers' function below.
     *
     * The function is expected to return an INTEGER_ARRAY.
     * The function accepts following parameters:
     *  1. 2D_STRING_ARRAY cacheEntries - each entry: [timestamp, modelId, predictionValue]
     *  2. 2D_STRING_ARRAY queries - each query: [modelId, timestamp]
     */
    public static List<Integer> getQueryAnswers(List<List<String>> cacheEntries, List<List<String>> queries) {
        // Build a map: (modelId, timestamp) -> predictionValue
        Map<String, Integer> cache = new HashMap<>();
        for (List<String> entry : cacheEntries) {
            String timestamp = entry.get(0);
            String modelId = entry.get(1);
            int predictionValue = Integer.parseInt(entry.get(2));
            String key = modelId + "|" + timestamp;  // Composite key for O(1) lookup
            cache.put(key, predictionValue);
        }

        // For each query, look up the prediction value
        List<Integer> result = new ArrayList<>();
        for (List<String> query : queries) {
            String modelId = query.get(0);
            String timestamp = query.get(1);
            String key = modelId + "|" + timestamp;
            result.add(cache.get(key));
        }
        return result;
    }
}

public class Solution {
    public static void main(String[] args) throws IOException {
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(System.in));
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(System.getenv("OUTPUT_PATH")));

        int cacheEntriesRows = Integer.parseInt(bufferedReader.readLine().trim());
        int cacheEntriesColumns = Integer.parseInt(bufferedReader.readLine().trim());

        List<List<String>> cacheEntries = new ArrayList<>();
        IntStream.range(0, cacheEntriesRows).forEach(i -> {
            try {
                cacheEntries.add(
                    Stream.of(bufferedReader.readLine().replaceAll("\\s+$", "").split(" "))
                        .collect(Collectors.toList())
                );
            } catch (IOException ex) {
                throw new RuntimeException(ex);
            }
        });

        int queriesRows = Integer.parseInt(bufferedReader.readLine().trim());
        int queriesColumns = Integer.parseInt(bufferedReader.readLine().trim());

        List<List<String>> queries = new ArrayList<>();
        IntStream.range(0, queriesRows).forEach(i -> {
            try {
                queries.add(
                    Stream.of(bufferedReader.readLine().replaceAll("\\s+$", "").split(" "))
                        .collect(Collectors.toList())
                );
            } catch (IOException ex) {
                throw new RuntimeException(ex);
            }
        });

        List<Integer> result = Result.getQueryAnswers(cacheEntries, queries);

        bufferedWriter.write(result.stream()
            .map(Object::toString)
            .collect(Collectors.joining("\n")) + "\n");

        bufferedReader.close();
        bufferedWriter.close();
    }
}
