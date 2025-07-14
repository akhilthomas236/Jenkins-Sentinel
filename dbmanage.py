#!/usr/bin/env python3
"""Database management script for the Jenkins Build Analyzer."""
import asyncio
import typer
from loguru import logger

from app.core.config import Settings
from app.services.database import DatabaseService

app = typer.Typer()

@app.command()
def init():
    """Initialize the database and run all migrations."""
    try:
        settings = Settings()
        db = DatabaseService(settings)
        asyncio.run(db.init_db())
        typer.echo("Database initialized successfully")
    except Exception as e:
        typer.echo(f"Error initializing database: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def status():
    """Show current migration status."""
    from alembic.config import Config
    from alembic.command import current
    
    try:
        alembic_cfg = Config("alembic.ini")
        current(alembic_cfg)
    except Exception as e:
        typer.echo(f"Error checking migration status: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def migrate():
    """Run database migrations."""
    from alembic.config import Config
    from alembic.command import upgrade
    
    try:
        alembic_cfg = Config("alembic.ini")
        upgrade(alembic_cfg, "head")
        typer.echo("Database migrations completed successfully")
    except Exception as e:
        typer.echo(f"Error running migrations: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def rollback():
    """Rollback the last migration."""
    from alembic.config import Config
    from alembic.command import downgrade
    
    try:
        alembic_cfg = Config("alembic.ini")
        downgrade(alembic_cfg, "-1")
        typer.echo("Successfully rolled back last migration")
    except Exception as e:
        typer.echo(f"Error rolling back migration: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def cleanup(pattern_ttl_days: int = 30, analysis_ttl_days: int = 7):
    """Clean up old data from the database."""
    try:
        settings = Settings()
        db = DatabaseService(settings)
        asyncio.run(db.cleanup_old_data(pattern_ttl_days, analysis_ttl_days))
        typer.echo("Database cleanup completed successfully")
    except Exception as e:
        typer.echo(f"Error cleaning up database: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
