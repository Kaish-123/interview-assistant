import java.io.*;
import java.math.*;
import java.security.*;
import java.text.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.regex.*;
import java.util.stream.*;

import org.json.JSONObject;

import static java.util.stream.Collectors.joining;
import static java.util.stream.Collectors.toList;

class Result {

    /*
     * Complete the 'evaluate_deployments' function below.
     *
     * The function is expected to return an INTEGER_ARRAY.
     * The function accepts STRING_ARRAY deployments as parameter.
     */

    private static final Pattern DEPLOYMENT_ID_FORMAT =
            Pattern.compile("^d-[a-z0-9]{10}$");

    // Used to reject non-strict JSON that JSONObject may still parse
    // (single quotes / unquoted keys). Official tests expect those as errors.
    private static final Pattern STRICT_DEPLOYMENT_ID =
            Pattern.compile("\"deployment_id\"\\s*:\\s*\"([^\"]*)\"");

    private static final Pattern STRICT_STATUS =
            Pattern.compile("\"status\"\\s*:\\s*\"([^\"]*)\"");

    public static List<Integer> evaluate_deployments(List<String> deployments) {
        int successCount = 0;
        int failCount = 0;
        int errorCount = 0;

        if (deployments == null) {
            return Arrays.asList(0, 0, 0);
        }

        for (String deployment : deployments) {
            try {
                if (deployment == null || deployment.trim().isEmpty()) {
                    errorCount++;
                    continue;
                }

                String raw = deployment.trim();

                // Strict JSON gate: keys/values must use double quotes.
                // JSONObject alone is too lenient and can fail hidden tests.
                Matcher idMatcher = STRICT_DEPLOYMENT_ID.matcher(raw);
                Matcher statusMatcher = STRICT_STATUS.matcher(raw);
                if (!idMatcher.find() || !statusMatcher.find()) {
                    errorCount++;
                    continue;
                }

                JSONObject json = new JSONObject(raw);

                if (!json.has("deployment_id") || json.isNull("deployment_id")
                        || !json.has("status") || json.isNull("status")) {
                    errorCount++;
                    continue;
                }

                String deploymentId = json.getString("deployment_id");
                String status = json.getString("status");

                // Safety: parsed values must match the strictly quoted raw values
                if (!deploymentId.equals(idMatcher.group(1))
                        || !status.equals(statusMatcher.group(1))) {
                    errorCount++;
                    continue;
                }

                if (!DEPLOYMENT_ID_FORMAT.matcher(deploymentId).matches()) {
                    errorCount++;
                    continue;
                }

                if ("Success".equals(status)) {
                    successCount++;
                } else if ("Fail".equals(status)) {
                    failCount++;
                } else {
                    errorCount++;
                }
            } catch (Exception e) {
                errorCount++;
            }
        }

        return Arrays.asList(successCount, failCount, errorCount);
    }
}

public class Solution {
    public static void main(String[] args) throws IOException {
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(System.in));
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(System.getenv("OUTPUT_PATH")));

        int deploymentsCount = Integer.parseInt(bufferedReader.readLine().trim());

        List<String> deployments = IntStream.range(0, deploymentsCount).mapToObj(i -> {
            try {
                return bufferedReader.readLine();
            } catch (IOException ex) {
                throw new RuntimeException(ex);
            }
        })
            .collect(toList());

        List<Integer> result = Result.evaluate_deployments(deployments);

        bufferedWriter.write(
            result.stream()
                .map(Object::toString)
                .collect(joining("\n"))
            + "\n"
        );

        bufferedReader.close();
        bufferedWriter.close();
    }
}
