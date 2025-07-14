package io.jenkins.plugins.buildanalyzer;

import hudson.Extension;
import jenkins.model.GlobalConfiguration;
import org.kohsuke.stapler.DataBoundSetter;

@Extension
public class BuildAnalyzerGlobalConfig extends GlobalConfiguration {
    private String analyzerUrl = "http://build-analyzer:8000";
    private boolean enableRealTimeAnalysis = false;
    private boolean analyzeAllBuilds = true;
    private String excludeJobs = "";

    public BuildAnalyzerGlobalConfig() {
        load();
    }

    public String getAnalyzerUrl() {
        return analyzerUrl;
    }

    @DataBoundSetter
    public void setAnalyzerUrl(String analyzerUrl) {
        this.analyzerUrl = analyzerUrl;
        save();
    }

    public boolean isEnableRealTimeAnalysis() {
        return enableRealTimeAnalysis;
    }

    @DataBoundSetter
    public void setEnableRealTimeAnalysis(boolean enableRealTimeAnalysis) {
        this.enableRealTimeAnalysis = enableRealTimeAnalysis;
        save();
    }

    public boolean isAnalyzeAllBuilds() {
        return analyzeAllBuilds;
    }

    @DataBoundSetter
    public void setAnalyzeAllBuilds(boolean analyzeAllBuilds) {
        this.analyzeAllBuilds = analyzeAllBuilds;
        save();
    }

    public String getExcludeJobs() {
        return excludeJobs;
    }

    @DataBoundSetter
    public void setExcludeJobs(String excludeJobs) {
        this.excludeJobs = excludeJobs;
        save();
    }
}
