import java.util.HashMap;
import java.util.Map;

class Solution {

    /** Find the length of the longest substring without repeating characters. */
    public static int lengthOfLongestSubstring(String s) {
        Map<Character, Integer> lastIndex = new HashMap<>();
        int maxLen = 0;
        int left = 0;

        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (lastIndex.containsKey(c) && lastIndex.get(c) >= left) {
                left = lastIndex.get(c) + 1;
            }
            lastIndex.put(c, right);
            maxLen = Math.max(maxLen, right - left + 1);
        }

        return maxLen;
    }

    /** Returns true if the tests pass. Otherwise, returns false. */
    public static boolean doTestsPass() {
        boolean result = true;
        result &= lengthOfLongestSubstring("abcabcbb") == 3;
        result &= lengthOfLongestSubstring("bbbbb") == 1;
        result &= lengthOfLongestSubstring("pwwkew") == 3;
        result &= lengthOfLongestSubstring("") == 0; // empty string
        result &= lengthOfLongestSubstring(" ") == 1; // single space
        result &= lengthOfLongestSubstring("au") == 2; // no repeats
        result &= lengthOfLongestSubstring("dvdf") == 3; // "vdf"
        return result;
    }

    public static void main(String[] args) {
        if (doTestsPass()) {
            System.out.println("All tests pass");
        } else {
            System.out.println("Tests fail.");
        }
    }
}
