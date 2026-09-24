/**
 * Beginner piano (right hand only).
 *
 * You can cover five consecutive keys: the thumb key and the four keys to
 * its right. Notes are numbered left-to-right starting at 1. Play the piece
 * in order while minimizing how many times you reposition your hand.
 *
 * Fingers in a position: 0 thumb, 1 index, 2 middle, 3 ring, 4 pinky.
 * For each stretch that fits one 5-key window (max - min <= 4), the thumb
 * sits on the lowest note in that stretch, so finger = note - min.
 *
 * Examples:
 *   [1, 2, 3, 4, 5, 4, 3, 2, 1]     => [0, 1, 2, 3, 4, 3, 2, 1, 0]
 *   [10, 9, 8, 7, 6, 5, 4, 3, 2, 1] => [4, 3, 2, 1, 0, 4, 3, 2, 1, 0]
 */
public class CountHandMoves {

    private static final int HAND_SPAN = 4; // 5 keys: [L, L+4]

    /**
     * For each note, which finger plays it (thumb = 0 ... pinky = 4).
     */
    public static int[] fingersForNotes(int[] notes) {
        if (notes == null || notes.length == 0) {
            return new int[0];
        }

        int[] fingers = new int[notes.length];
        int segStart = 0;
        int low = notes[0];
        int high = notes[0];

        for (int i = 1; i <= notes.length; i++) {
            boolean flush = (i == notes.length);
            if (!flush) {
                int newLow = Math.min(low, notes[i]);
                int newHigh = Math.max(high, notes[i]);
                if (newHigh - newLow > HAND_SPAN) {
                    flush = true;
                } else {
                    low = newLow;
                    high = newHigh;
                }
            }

            if (flush) {
                for (int j = segStart; j < i; j++) {
                    fingers[j] = notes[j] - low;
                }
                if (i < notes.length) {
                    segStart = i;
                    low = notes[i];
                    high = notes[i];
                }
            }
        }
        return fingers;
    }

    public static int countHandMoves(int[] notes) {
        if (notes == null || notes.length == 0) {
            return 0;
        }

        int moveCount = 0;
        int start = notes[0];
        int end = notes[0];

        for (int note : notes) {
            int newStart = Math.min(start, note);
            int newEnd = Math.max(end, note);
            if (newEnd - newStart > HAND_SPAN) {
                start = note;
                end = note;
                moveCount++;
            } else {
                start = newStart;
                end = newEnd;
            }
        }
        return moveCount;
    }

    public static void main(String[] args) {
        int[][] examples = {
            {1, 2, 3, 4, 5, 4, 3, 2, 1},
            {10, 9, 8, 7, 6, 5, 4, 3, 2, 1},
            {6, 5, 4, 3, 2, 7, 8, 9, 10},
            {1, 6, 11},
        };

        for (int[] notes : examples) {
            System.out.println("notes:   " + java.util.Arrays.toString(notes));
            System.out.println("fingers: " + java.util.Arrays.toString(fingersForNotes(notes))
                    + "  (moves: " + countHandMoves(notes) + ")");
            System.out.println();
        }
    }
}
