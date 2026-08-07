import java.util.*;

class Result {

    /*
     * Complete the 'manageServerLogs' function below.
     *
     * The function is expected to return an INTEGER.
     * The function accepts STRING_ARRAY serverLogs as parameter.
     *
     * Rules:
     * 1. Logs are in request order. If current time < previous time => new day.
     * 2. At most 10 requests per minute per day; the 11th+ at that minute
     *    must move to the next day(s).
     */
    public static int manageServerLogs(List<String> serverLogs) {
        if (serverLogs == null || serverLogs.isEmpty()) {
            return 0;
        }

        int days = 1;
        int prevMinutes = toMinutes(serverLogs.get(0));
        int countAtMinute = 1;

        for (int i = 1; i < serverLogs.size(); i++) {
            int currMinutes = toMinutes(serverLogs.get(i));

            if (currMinutes < prevMinutes) {
                // Time went backwards => must be a new day
                days++;
                countAtMinute = 1;
                prevMinutes = currMinutes;
            } else if (currMinutes == prevMinutes) {
                // Same minute: capacity is 10 per day
                if (countAtMinute == 10) {
                    days++;
                    countAtMinute = 1;
                    // prevMinutes stays the same (still that minute on the new day)
                } else {
                    countAtMinute++;
                }
            } else {
                // Later time on the same day
                prevMinutes = currMinutes;
                countAtMinute = 1;
            }
        }

        return days;
    }

    /**
     * Convert "[hh:mm a.m.]: ..." or "[hh:mm p.m.]: ..." to minutes from midnight [0, 1439].
     * 12:xx a.m. -> 00:xx, 12:xx p.m. -> 12:xx
     */
    private static int toMinutes(String log) {
        // Format: [hh:mm a.m.]: message  OR  [hh:mm p.m.]: message
        int close = log.indexOf(']');
        String timePart = log.substring(1, close).trim(); // "hh:mm a.m." or "hh:mm p.m."

        int hour = Integer.parseInt(timePart.substring(0, 2));
        int minute = Integer.parseInt(timePart.substring(3, 5));
        boolean isPM = timePart.charAt(6) == 'p' || timePart.charAt(6) == 'P';

        if (hour == 12) {
            hour = 0; // 12 a.m. -> 0, 12 p.m. temporarily 0 then +12 below
        }
        if (isPM) {
            hour += 12;
        }

        return hour * 60 + minute;
    }
}

public class ManageServerLogs {
    public static void main(String[] args) {
        // Sample from problem statement
        assertEq(2, Result.manageServerLogs(Arrays.asList(
                "[05:00 a.m.]: Server is started",
                "[05:00 a.m.]: Rescan initialized",
                "[01:13 p.m.]: Request processed",
                "[01:10 p.m.]: Request processed",
                "[11:40 p.m.]: Rescan completed"
        )));

        // Sample Case 0
        assertEq(3, Result.manageServerLogs(Arrays.asList(
                "[09:00 a.m.]: User logged in",
                "[08:00 a.m.]: User logged in",
                "[07:00 a.m.]: User logged in"
        )));

        // Sample Case 1: 11 logs at same minute => 2 days (10 + 1)
        List<String> eleven = new ArrayList<>();
        for (int i = 1; i <= 10; i++) {
            eleven.add("[05:00 a.m.]: Server" + i + " is started");
        }
        eleven.add("[05:00 a.m.]: Server1 is interrupted");
        assertEq(2, Result.manageServerLogs(eleven));

        // Exactly 10 at same minute => 1 day
        List<String> ten = new ArrayList<>();
        for (int i = 0; i < 10; i++) {
            ten.add("[05:00 a.m.]: log");
        }
        assertEq(1, Result.manageServerLogs(ten));

        // 21 at same minute => 3 days (10 + 10 + 1)
        List<String> twentyOne = new ArrayList<>();
        for (int i = 0; i < 21; i++) {
            twentyOne.add("[05:00 a.m.]: log");
        }
        assertEq(3, Result.manageServerLogs(twentyOne));

        // Single log
        assertEq(1, Result.manageServerLogs(Collections.singletonList(
                "[12:00 a.m.]: start"
        )));

        // Strictly increasing same day
        assertEq(1, Result.manageServerLogs(Arrays.asList(
                "[12:00 a.m.]: a",
                "[12:01 a.m.]: b",
                "[11:59 a.m.]: c",
                "[12:00 p.m.]: d",
                "[12:01 p.m.]: e",
                "[11:59 p.m.]: f"
        )));

        // Equal times allowed up to 10
        assertEq(1, Result.manageServerLogs(Arrays.asList(
                "[01:00 p.m.]: a",
                "[01:00 p.m.]: b",
                "[01:00 p.m.]: c"
        )));

        // Midnight wrap: late night then early morning
        assertEq(2, Result.manageServerLogs(Arrays.asList(
                "[11:59 p.m.]: a",
                "[12:00 a.m.]: b"
        )));

        // 12 a.m. vs 12 p.m. ordering
        assertEq(1, Result.manageServerLogs(Arrays.asList(
                "[12:00 a.m.]: midnight",
                "[12:00 p.m.]: noon"
        )));
        assertEq(2, Result.manageServerLogs(Arrays.asList(
                "[12:00 p.m.]: noon",
                "[12:00 a.m.]: midnight"
        )));

        // Overflow then later same day on new day
        List<String> overflowThenLater = new ArrayList<>();
        for (int i = 0; i < 11; i++) {
            overflowThenLater.add("[01:00 p.m.]: x");
        }
        overflowThenLater.add("[02:00 p.m.]: y");
        assertEq(2, Result.manageServerLogs(overflowThenLater));

        // Overflow then time goes backwards => another day
        List<String> overflowThenBack = new ArrayList<>();
        for (int i = 0; i < 11; i++) {
            overflowThenBack.add("[02:00 p.m.]: x");
        }
        overflowThenBack.add("[01:00 p.m.]: y");
        assertEq(3, Result.manageServerLogs(overflowThenBack));

        // Non-decreasing across day after overflow of equal times
        assertEq(1, Result.manageServerLogs(Arrays.asList(
                "[09:00 a.m.]: a",
                "[10:00 a.m.]: b",
                "[10:00 a.m.]: c"
        )));

        System.out.println("All tests passed");
    }

    private static void assertEq(int expected, int actual) {
        if (expected != actual) {
            throw new AssertionError("Expected " + expected + " but got " + actual);
        }
    }
}
