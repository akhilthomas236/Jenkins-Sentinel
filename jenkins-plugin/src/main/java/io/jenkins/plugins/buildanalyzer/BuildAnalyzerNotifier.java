package io.jenkins.plugins.buildanalyzer;

import hudson.Extension;
import hudson.model.Run;
import hudson.model.TaskListener;
import hudson.model.listeners.RunListener;
import jenkins.model.Jenkins;
import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

@Extension
public class BuildAnalyzerNotifier extends RunListener<Run<?, ?>> {
    private final HttpClient client = HttpClient.newHttpClient();
    private final String analyzerUrl;

    public BuildAnalyzerNotifier() {
        // Get URL from Jenkins configuration
        analyzerUrl = Jenkins.get().getDescriptor(BuildAnalyzerGlobalConfig.class)
                           .getAnalyzerUrl();
    }

    @Override
    public void onCompleted(Run<?, ?> run, TaskListener listener) {
        // Automatically notify analyzer when any build completes
        try {
            notifyAnalyzer(run, listener);
        } catch (IOException e) {
            listener.error("Failed to notify build analyzer: " + e.getMessage());
        }
    }

    @Override
    public void onStarted(Run<?, ?> run, TaskListener listener) {
        // Optionally notify when build starts for real-time analysis
        try {
            notifyAnalyzerStart(run, listener);
        } catch (IOException e) {
            listener.error("Failed to notify build analyzer start: " + e.getMessage());
        }
    }

    private void notifyAnalyzer(Run<?, ?> run, TaskListener listener) throws IOException {
        String payload = String.format("""
            {
                "jobName": "%s",
                "buildNumber": %d,
                "result": "%s",
                "timestamp": %d,
                "duration": %d,
                "url": "%s"
            }""",
            run.getParent().getFullName(),
            run.getNumber(),
            run.getResult().toString(),
            run.getTimeInMillis(),
            run.getDuration(),
            run.getUrl()
        );

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(analyzerUrl + "/api/v1/analyze"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(payload))
            .build();

        try {
            HttpResponse<String> response = client.send(request, 
                HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                listener.error("Build analyzer returned status: " + response.statusCode());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            listener.error("Build analyzer notification interrupted: " + e.getMessage());
        }
    }

    private void notifyAnalyzerStart(Run<?, ?> run, TaskListener listener) throws IOException {
        // Similar to notifyAnalyzer but for build start events
    }
}
