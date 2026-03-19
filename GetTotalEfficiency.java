import java.io.*;
import java.util.*;

class Result {
    /*
     * Complete the 'getTotalEfficiency' function below.
     *
     * The function is expected to return a LONG_INTEGER.
     * The function accepts INTEGER_ARRAY skill as parameter.
     */
    public static long getTotalEfficiency(List<Integer> skill) {
        int n = skill.size();
        
        // If array is empty or odd length (shouldn't happen per constraints), return -1
        if (n == 0 || n % 2 != 0) {
            return -1;
        }
        
        // Sort the skill array
        Collections.sort(skill);
        
        // The target sum must be: smallest + largest
        // This is because we need to pair smallest with largest to get equal sums
        int targetSum = skill.get(0) + skill.get(n - 1);
        
        // Use two pointers: one from start, one from end
        long totalEfficiency = 0;
        int left = 0;
        int right = n - 1;
        
        while (left < right) {
            int currentSum = skill.get(left) + skill.get(right);
            
            // If current pair doesn't match target sum, return -1
            if (currentSum != targetSum) {
                return -1;
            }
            
            // Calculate efficiency (product) and add to total
            totalEfficiency += (long) skill.get(left) * skill.get(right);
            
            // Move pointers
            left++;
            right--;
        }
        
        return totalEfficiency;
    }
}

public class Solution {
    public static void main(String[] args) throws IOException {
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(System.in));
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(System.getenv("OUTPUT_PATH")));
        
        int skillCount = Integer.parseInt(bufferedReader.readLine().trim());
        
        List<Integer> skill = new ArrayList<>();
        
        for (int i = 0; i < skillCount; i++) {
            int skillItem = Integer.parseInt(bufferedReader.readLine().trim());
            skill.add(skillItem);
        }
        
        long result = Result.getTotalEfficiency(skill);
        
        bufferedWriter.write(String.valueOf(result));
        bufferedWriter.newLine();
        
        bufferedReader.close();
        bufferedWriter.close();
    }
}
