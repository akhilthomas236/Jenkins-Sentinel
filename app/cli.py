"""Command Line Interface for Jenkins Build Analyzer."""
from typing import Optional, List
import asyncio
from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.jenkins_client import JenkinsClient
from app.services.bedrock_client import BedrockClient
from app.services.build_analyzer import BuildAnalyzer
from app.services.agent_manager import AgentManager

app = typer.Typer(help="Jenkins Build Analyzer CLI")
console = Console()

# Shared service instances
settings: Optional[Settings] = None
agent_manager: Optional[AgentManager] = None

@app.callback()
def init_services():
    """Initialize shared services."""
    global settings, agent_manager
    if not settings:
        settings = Settings()
        configure_logging(settings)
        
        # Initialize services
        jenkins_client = JenkinsClient(settings)
        bedrock_client = BedrockClient(settings)
        build_analyzer = BuildAnalyzer(jenkins_client, bedrock_client)
        agent_manager = AgentManager(jenkins_client, bedrock_client, build_analyzer)

@app.command()
def start(
    monitor: bool = typer.Option(True, "--monitor/--no-monitor", help="Start the monitoring agent"),
    jobs: List[str] = typer.Option(None, "--job", "-j", help="Monitor specific jobs only"),
):
    """Start the Jenkins Build Analyzer agent."""
    try:
        if monitor:
            console.print("[green]Starting Jenkins Build Analyzer...[/green]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Initializing monitoring tasks...", total=None)
                # Run the agent manager
                asyncio.run(agent_manager.start())
        else:
            console.print("[yellow]Running in analysis-only mode[/yellow]")
            
    except KeyboardInterrupt:
        console.print("[yellow]Shutting down...[/yellow]")
    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
        raise typer.Exit(1)

@app.command()
def analyze(
    job_name: str = typer.Argument(..., help="Jenkins job name"),
    build_number: int = typer.Argument(..., help="Build number to analyze"),
    compare_last: bool = typer.Option(True, "--compare/--no-compare", help="Compare with last successful build"),
):
    """Analyze a specific Jenkins build."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Analyzing {job_name} #{build_number}...", total=None)
            analysis = asyncio.run(agent_manager.analyzer.analyze_build(job_name, build_number))
            progress.update(task, completed=True)
            
        # Display results in a table
        table = Table(title=f"Build Analysis Results: {job_name} #{build_number}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Result", analysis.build_info.result)
        table.add_row("Severity", analysis.severity)
        table.add_row("Confidence", f"{analysis.confidence * 100:.1f}%")
        
        if analysis.recommendations:
            table.add_row("Recommendations", "\\n".join(analysis.recommendations))
            
        console.print(table)
            
    except Exception as e:
        logger.error(f"Failed to analyze build: {e}")
        raise typer.Exit(1)

@app.command()
def patterns(
    job_name: Optional[str] = typer.Argument(None, help="Filter patterns by job name"),
):
    """View learned build failure patterns."""
    try:
        patterns = agent_manager.pattern_database
        if job_name:
            patterns = {job_name: patterns.get(job_name, [])}
            
        table = Table(title="Learned Build Patterns")
        table.add_column("Job", style="cyan")
        table.add_column("Pattern", style="green")
        table.add_column("Frequency", justify="right")
        table.add_column("Last Seen", justify="right")
        
        for job, job_patterns in patterns.items():
            for pattern in job_patterns:
                table.add_row(
                    job,
                    pattern['pattern'],
                    str(pattern['frequency']),
                    pattern['last_seen'].strftime("%Y-%m-%d %H:%M")
                )
                
        console.print(table)
            
    except Exception as e:
        logger.error(f"Failed to fetch patterns: {e}")
        raise typer.Exit(1)

@app.command()
def actions(
    job_name: Optional[str] = typer.Argument(None, help="Filter actions by job name"),
    build_number: Optional[int] = typer.Option(None, "--build", "-b", help="Filter by build number"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of actions to show"),
):
    """View automated actions taken by the agent."""
    try:
        actions = []
        for key, build_actions in agent_manager.action_history.items():
            job, build = key.split('#')
            if job_name and job != job_name:
                continue
            if build_number and int(build) != build_number:
                continue
            
            for action in build_actions:
                actions.append({
                    'job': job,
                    'build': build,
                    'type': action['type'],
                    'result': action['result'],
                    'timestamp': datetime.fromisoformat(action['timestamp'])
                })
                
        # Sort by timestamp descending and limit
        actions.sort(key=lambda x: x['timestamp'], reverse=True)
        actions = actions[:limit]
            
        table = Table(title="Agent Actions")
        table.add_column("Time", style="cyan")
        table.add_column("Job", style="blue")
        table.add_column("Build", justify="right")
        table.add_column("Action", style="green")
        table.add_column("Result")
        
        for action in actions:
            table.add_row(
                action['timestamp'].strftime("%Y-%m-%d %H:%M"),
                action['job'],
                action['build'],
                action['type'],
                action['result']
            )
                
        console.print(table)
            
    except Exception as e:
        logger.error(f"Failed to fetch actions: {e}")
        raise typer.Exit(1)

@app.command()
def stats():
    """Show system statistics and metrics."""
    try:
        stats_table = Table(title="System Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row(
            "Active Monitors",
            str(len(agent_manager.active_monitors))
        )
        stats_table.add_row(
            "Cached Analyses",
            str(len(agent_manager.analysis_cache))
        )
        stats_table.add_row(
            "Known Patterns",
            str(sum(len(patterns) for patterns in agent_manager.pattern_database.values()))
        )
        stats_table.add_row(
            "Actions Taken",
            str(sum(len(actions) for actions in agent_manager.action_history.values()))
        )
        stats_table.add_row(
            "Learning Enabled",
            "✓" if agent_manager.learning_enabled else "✗"
        )
        
        console.print(stats_table)
            
    except Exception as e:
        logger.error(f"Failed to fetch statistics: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
