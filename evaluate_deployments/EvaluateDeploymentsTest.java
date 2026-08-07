import java.util.*;

public class EvaluateDeploymentsTest {
    private static int passed = 0, failed = 0;

    public static void main(String[] args) {
        // Sample cases (must keep passing)
        check(Arrays.asList(1, 1, 0), Arrays.asList(
            "{\"deployment_id\": \"d-12345678ab\", \"status\": \"Success\"}",
            "{\"deployment_id\": \"d-09876543cd\", \"status\": \"Fail\"}"
        ), "Sample 0");

        check(Arrays.asList(1, 0, 1), Arrays.asList(
            "{\"deployment_id\": \"d-12345678ab\", \"status\": \"Success\"}",
            "{\"deployment_id\": \"d-12345678cd\", \"status\": \"ABCDE\"}"
        ), "Sample 1");

        // Hidden-test style: org.json would ACCEPT these, strict JSON must ERROR
        check(Arrays.asList(0, 0, 1), Arrays.asList(
            "{'deployment_id': 'd-12345678ab', 'status': 'Success'}"
        ), "Single quotes (strict JSON reject)");

        check(Arrays.asList(0, 0, 1), Arrays.asList(
            "{deployment_id: \"d-12345678ab\", status: \"Success\"}"
        ), "Unquoted keys (strict JSON reject)");

        // All-digit suffix should still be valid per a-z0-9 rule
        check(Arrays.asList(1, 0, 0), Arrays.asList(
            "{\"deployment_id\": \"d-1234567890\", \"status\": \"Success\"}"
        ), "All-digit deployment_id");

        // Existing edge cases
        check(Arrays.asList(0, 0, 0), Collections.emptyList(), "Empty");
        check(Arrays.asList(0, 0, 2), Arrays.asList(
            "{\"deployment_id\": \"d-12345678AB\", \"status\": \"Success\"}",
            "{\"deployment_id\": \"d-12345678ab\", \"status\": \"success\"}"
        ), "Bad id case / bad status case");

        check(Arrays.asList(1, 1, 0), Arrays.asList(
            "{\"status\":\"Success\",\"deployment_id\":\"d-12345678ab\"}",
            "{ \"deployment_id\" : \"d-09876543cd\" , \"status\" : \"Fail\" }"
        ), "Field order / whitespace");

        System.out.println("Passed: " + passed + ", Failed: " + failed);
        if (failed > 0) System.exit(1);
    }

    private static void check(List<Integer> expected, List<String> input, String name) {
        List<Integer> actual = Result.evaluate_deployments(input);
        if (Objects.equals(expected, actual)) {
            passed++;
            System.out.println("PASS: " + name + " -> " + actual);
        } else {
            failed++;
            System.out.println("FAIL: " + name + " expected " + expected + " got " + actual);
        }
    }
}
