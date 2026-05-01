import java.util.*;
import org.apache.commons.lang3.tuple.Pair;

enum Attn {
    REQUIRED,
    OPTIONAL
}

public class Solution {
    public static void main(String[] args) {
        List<Pair<String, Attn>> exampleInput = List.of(
            Pair.of("harvey@example.com", Attn.OPTIONAL), // appears first as OPTIONAL
            Pair.of("mike@example.com", Attn.REQUIRED),
            Pair.of("harvey@example.com", Attn.REQUIRED), // REQUIRED wins
            Pair.of("donna@example.com", Attn.OPTIONAL)
        );

        Map<Attn, List<String>> expectedOutput = Map.of(
            Attn.REQUIRED, List.of("mike@example.com", "harvey@example.com"),
            Attn.OPTIONAL, List.of("donna@example.com")
        );

        Map<Attn, List<String>> result = categorizeEmailsByAttendance(exampleInput);

        System.out.println("Expected: " + result.equals(expectedOutput));
        System.out.println("REQUIRED: " + result.get(Attn.REQUIRED));
        System.out.println("OPTIONAL: " + result.get(Attn.OPTIONAL));
    }

    public static Map<Attn, List<String>> categorizeEmailsByAttendance(List<Pair<String, Attn>> attendees) {
        // LinkedHashSet preserves insertion order while removing duplicates.
        LinkedHashSet<String> required = new LinkedHashSet<>();
        LinkedHashSet<String> optional = new LinkedHashSet<>();

        for (Pair<String, Attn> attendee : attendees) {
            String email = attendee.getLeft();
            Attn attendanceType = attendee.getRight();

            if (attendanceType == Attn.REQUIRED) {
                required.add(email);
                optional.remove(email); // REQUIRED takes precedence if seen later
            } else {
                if (!required.contains(email)) {
                    optional.add(email);
                }
            }
        }

        Map<Attn, List<String>> resultMap = new HashMap<>();
        resultMap.put(Attn.REQUIRED, new ArrayList<>(required));
        resultMap.put(Attn.OPTIONAL, new ArrayList<>(optional));
        return resultMap;
    }
}
