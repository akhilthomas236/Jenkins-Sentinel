# Build Analyzer Plugin Configuration

No explicit pipeline configuration is needed! The Build Analyzer plugin automatically monitors all builds and sends them for analysis. Here's how it works:

## Automatic Integration

1. **Build Event Listeners**
   - Automatically captures all build events
   - No pipeline modifications needed
   - Works with all job types (Freestyle, Pipeline, etc.)

2. **Global Configuration**
   - Configure once in Jenkins settings
   - Applies to all jobs by default
   - Can exclude specific jobs if needed

## Configuration Options

In Jenkins, go to `Manage Jenkins` → `Configure System` → `Build Analyzer Configuration`:

1. **Analyzer URL**
   - URL of your analyzer service
   - Default: `http://build-analyzer:8000`

2. **Real-time Analysis**
   - Enable for immediate analysis during builds
   - Disabled by default

3. **Analyze All Builds**
   - Enable to analyze all builds
   - Disable to only analyze failures
   - Enabled by default

4. **Exclude Jobs**
   - Comma-separated patterns of jobs to exclude
   - Example: `test-.*,temporary-.*`

## How It Works

1. **Build Start**
   ```mermaid
   sequenceDiagram
       participant J as Jenkins
       participant P as Plugin
       participant A as Analyzer
       
       J->>P: Build Started
       P->>A: Notify Build Start
       A->>A: Initialize Analysis
   ```

2. **Build Completion**
   ```mermaid
   sequenceDiagram
       participant J as Jenkins
       participant P as Plugin
       participant A as Analyzer
       
       J->>P: Build Completed
       P->>A: Send Build Data
       A->>A: Analyze Build
       A->>J: Update Build Page
   ```

## Kubernetes Integration

In Kubernetes, the plugin automatically discovers the analyzer service using K8s service discovery:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: build-analyzer
spec:
  selector:
    app: build-analyzer
  ports:
    - port: 8000
```

The plugin will automatically use `http://build-analyzer.default.svc.cluster.local:8000` as the analyzer URL.

## Optional: Manual Pipeline Integration

While not required, you can still explicitly use the analyzer in your pipelines for custom analysis:

```groovy
pipeline {
    // ... your pipeline config ...
    
    post {
        always {
            buildAnalyzer(
                detailed: true,  // More detailed analysis
                customQuery: "Check for memory leaks"  // Custom analysis focus
            )
        }
    }
}
```

## Troubleshooting

1. **Verify Plugin Installation**
   ```bash
   curl -X GET "${JENKINS_URL}/pluginManager/api/json?depth=1" | jq '.plugins[] | select(.shortName=="build-analyzer")'
   ```

2. **Check Analyzer Connection**
   ```bash
   curl -X GET "${ANALYZER_URL}/health"
   ```

3. **View Plugin Logs**
   - Go to `Manage Jenkins` → `System Log`
   - Add logger: `io.jenkins.plugins.buildanalyzer`

## Best Practices

1. **Resource Management**
   - Configure appropriate timeouts
   - Set reasonable analysis batch sizes
   - Monitor analyzer service load

2. **Security**
   - Use HTTPS for analyzer communication
   - Configure appropriate CORS settings
   - Use Jenkins credentials for authentication

3. **Monitoring**
   - Enable analyzer metrics
   - Monitor analysis queue length
   - Set up alerts for analyzer issues
