import java.io.*;
import java.math.*;
import java.security.*;
import java.text.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.regex.*;
import java.util.stream.*;
import static java.util.stream.Collectors.joining;
import static java.util.stream.Collectors.toList;

class Result {

    /*
     * Count substrings that contain only vowels and each vowel (a,e,i,o,u) at least once.
     * Sliding window: when window [start, end] has all 5 vowels, count one substring per
     * valid start, then shrink from the left.
     */
    public static long vowelsubstring(String s) {
        long count = 0;
        int start = 0;
        Map<Character, Integer> vowelFrequency = new HashMap<>();

        for (int end = 0; end < s.length(); end++) {
            char currentChar = s.charAt(end);

            if (isVowel(currentChar)) {
                vowelFrequency.put(currentChar, vowelFrequency.getOrDefault(currentChar, 0) + 1);

                while (vowelFrequency.size() == 5) {
                    // One substring ending at end for each valid start in [segmentStart, start]
                    count += 1;
                    char startChar = s.charAt(start);

                    if (isVowel(startChar)) {
                        int freq = vowelFrequency.get(startChar) - 1;
                        if (freq == 0) {
                            vowelFrequency.remove(startChar);
                        } else {
                            vowelFrequency.put(startChar, freq);
                        }
                    }
                    start++;
                }
            } else {
                vowelFrequency.clear();
                start = end + 1;
            }
        }
        return count;
    }

    private static boolean isVowel(char c) {
        return "aeiou".indexOf(c) >= 0;
    }
}

public class Solution {
    public static void main(String[] args) throws IOException {
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(System.in));
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(System.getenv("OUTPUT_PATH")));

        String s = bufferedReader.readLine();

        long result = Result.vowelsubstring(s);

        bufferedWriter.write(String.valueOf(result));
        bufferedWriter.newLine();

        bufferedReader.close();
        bufferedWriter.close();
    }
}
