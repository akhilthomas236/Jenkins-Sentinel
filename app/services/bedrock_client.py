"""Amazon Bedrock integration service for LLM-based build analysis."""
import json
from typing import Dict, Any, List, Optional
import boto3
from loguru import logger
from app.core.config import Settings
from app.models.build import BuildInfo, BuildAnalysis
from datetime import datetime

class BedrockClient:
    def __init__(self, settings: Settings):
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.model_id = settings.bedrock_model_id
        
    async def analyze_build(self, build: BuildInfo, last_success: Optional[BuildInfo] = None) -> BuildAnalysis:
        """Analyze a build using Amazon Bedrock LLM."""
        prompt = self._construct_analysis_prompt(build, last_success)
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'prompt': prompt,
                    'max_tokens_to_sample': 4000,
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'stop_sequences': ["\n\nHuman:"],
                    'anthropic_version': 'bedrock-2023-05-31'
                })
            )
            
            response_body = json.loads(response['body'].read().decode())
            
            # Extract the JSON from Claude's response
            completion = response_body.get('completion', '')
            try:
                # Find the JSON object in the completion
                start = completion.find('{')
                end = completion.rfind('}') + 1
                if start >= 0 and end > start:
                    analysis = json.loads(completion[start:end])
                else:
                    raise ValueError("No JSON found in response")
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
                
            return self._parse_analysis_response(analysis, build, last_success)
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {str(e)}")
            raise
    
    def _construct_analysis_prompt(self, build: BuildInfo, last_success: Optional[BuildInfo] = None) -> str:
        """Construct the prompt for build analysis."""
        prompt = f"\n\nHuman: You are a Jenkins build analysis expert. Please analyze the following build failure and provide structured insights.\n\nJenkins Build Details:\nBuild: {build.job_name} #{build.build_number}\nResult: {build.result}\n\nBuild Console Log:\n{build.console_log}\n\n"
        
        if last_success:
            prompt += f"Last Successful Build #{last_success.build_number} Console Log for Comparison:\n{last_success.console_log}\n\n"
            
        prompt += """Please analyze this build and:
1. Identify the main error patterns and their context
2. Note key differences from the successful build
3. Determine likely root causes
4. Provide specific recommendations for fixing the issue
5. Assign a severity level and confidence score

Provide your analysis as a JSON object with these fields:
{
    "error_patterns": [{"pattern": "error pattern", "context": "surrounding context"}],
    "differences": [{"type": "change type", "description": "what changed"}],
    "recommendations": ["specific action 1", "specific action 2"],
    "severity": "HIGH|MEDIUM|LOW",
    "confidence": 0.0-1.0
}

\n\nAssistant: I'll analyze the build and provide my findings in the requested JSON format.
"""
        return prompt
    
    def _parse_analysis_response(self, analysis: Dict[str, Any], build: BuildInfo, 
                               last_success: Optional[BuildInfo]) -> BuildAnalysis:
        """Parse the LLM response into a BuildAnalysis object."""
        return BuildAnalysis(
            build_info=build,
            last_success=last_success,
            error_patterns=analysis.get('error_patterns', []),
            differences=analysis.get('differences', []),
            recommendations=analysis.get('recommendations', []),
            severity=analysis.get('severity', 'LOW'),
            confidence=analysis.get('confidence', 0.5),
            timestamp=datetime.now()
        )
