"""Database service for the build analyzer."""
from typing import Optional, List, Dict, Any
import os
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from loguru import logger
import alembic.config
import alembic.command

from app.models.database import Base, Build, Analysis, Pattern, Action
from app.models.build import BuildInfo, BuildAnalysis
from app.core.config import Settings

class DatabaseService:
    def __init__(self, settings: Settings):
        """Initialize the database service."""
        self.settings = settings
        # SQLite for development, PostgreSQL for production
        if settings.env == "production":
            db_url = settings.database_url
        else:
            db_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "analyzer.db")
            db_url = f"sqlite+aiosqlite:///{db_path}"
            
        self.engine = create_async_engine(db_url, echo=settings.log_level == "DEBUG")
        self.session_maker = async_sessionmaker(self.engine, class_=AsyncSession)

    async def init_db(self):
        """Initialize the database schema and run migrations."""
        try:
            # Run migrations in a separate thread since Alembic doesn't support async
            def run_migrations():
                alembic_cfg = alembic.config.Config("alembic.ini")
                alembic.command.upgrade(alembic_cfg, "head")
            
            await asyncio.to_thread(run_migrations)
            logger.info("Database migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Error running database migrations: {e}")
            raise

    async def save_build(self, build_info: BuildInfo) -> int:
        """Save build information to the database."""
        async with self.session_maker() as session:
            build = Build.from_build_info(build_info)
            session.add(build)
            await session.commit()
            await session.refresh(build)
            return build.id
            
    async def save_analysis(self, analysis: BuildAnalysis, build_id: int,
                          last_success_id: Optional[int] = None) -> None:
        """Save build analysis results to the database."""
        async with self.session_maker() as session:
            db_analysis = Analysis.from_build_analysis(analysis, build_id, last_success_id)
            session.add(db_analysis)
            await session.commit()
            
    async def save_pattern(self, job_name: str, pattern: Dict[str, Any]) -> int:
        """Save a learned pattern to the database."""
        async with self.session_maker() as session:
            db_pattern = Pattern.from_dict(job_name, pattern)
            session.add(db_pattern)
            await session.commit()
            await session.refresh(db_pattern)
            return db_pattern.id
            
    async def save_action(self, build_id: int, action: Dict[str, Any],
                         pattern_id: Optional[int] = None) -> None:
        """Save an agent action to the database."""
        async with self.session_maker() as session:
            db_action = Action.from_dict(build_id, action, pattern_id)
            session.add(db_action)
            await session.commit()
            
    async def get_build(self, job_name: str, build_number: int) -> Optional[BuildInfo]:
        """Get build information from the database."""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Build).where(
                    Build.job_name == job_name,
                    Build.build_number == build_number
                )
            )
            build = result.scalar_one_or_none()
            if not build:
                return None
                
            return BuildInfo(
                job_name=build.job_name,
                build_number=build.build_number,
                result=build.result,
                timestamp=build.timestamp,
                duration=build.duration,
                parameters=build.parameters,
                url=build.url,
                console_log=build.console_log
            )
            
    async def get_analysis(self, job_name: str, build_number: int) -> Optional[BuildAnalysis]:
        """Get build analysis from the database."""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Analysis)
                .join(Build)
                .options(selectinload(Analysis.build))
                .where(
                    Build.job_name == job_name,
                    Build.build_number == build_number
                )
            )
            analysis = result.scalar_one_or_none()
            if not analysis:
                return None
                
            return BuildAnalysis(
                build_info=BuildInfo(
                    job_name=analysis.build.job_name,
                    build_number=analysis.build.build_number,
                    result=analysis.build.result,
                    timestamp=analysis.build.timestamp,
                    duration=analysis.build.duration,
                    parameters=analysis.build.parameters,
                    url=analysis.build.url,
                    console_log=analysis.build.console_log
                ),
                last_success=None,  # TODO: Load last success if needed
                error_patterns=analysis.error_patterns,
                differences=analysis.differences,
                recommendations=analysis.recommendations,
                severity=analysis.severity,
                confidence=analysis.confidence,
                timestamp=analysis.timestamp
            )
            
    async def get_patterns(self, job_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get learned patterns from the database."""
        async with self.session_maker() as session:
            query = select(Pattern).where(Pattern.is_active == True)
            if job_name:
                query = query.where(Pattern.job_name == job_name)
                
            result = await session.execute(query)
            patterns = result.scalars().all()
            
            pattern_dict: Dict[str, List[Dict[str, Any]]] = {}
            for pattern in patterns:
                if pattern.job_name not in pattern_dict:
                    pattern_dict[pattern.job_name] = []
                pattern_dict[pattern.job_name].append({
                    'pattern': pattern.pattern,
                    'frequency': pattern.frequency,
                    'last_seen': pattern.last_seen,
                    'solution': pattern.solution
                })
                
            return pattern_dict
            
    async def get_actions(self, job_name: Optional[str] = None,
                         build_number: Optional[int] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent actions from the database."""
        async with self.session_maker() as session:
            query = (
                select(Action)
                .join(Build)
                .options(selectinload(Action.build))
                .order_by(Action.timestamp.desc())
            )
            
            if job_name:
                query = query.where(Build.job_name == job_name)
            if build_number:
                query = query.where(Build.build_number == build_number)
                
            query = query.limit(limit)
            result = await session.execute(query)
            actions = result.scalars().all()
            
            return [{
                'job': action.build.job_name,
                'build': action.build.build_number,
                'type': action.type,
                'result': action.result,
                'timestamp': action.timestamp.isoformat()
            } for action in actions]
            
    async def cleanup_old_data(self, pattern_ttl_days: int = 30,
                             analysis_ttl_days: int = 7) -> None:
        """Clean up old data from the database."""
        async with self.session_maker() as session:
            # Deactivate old patterns
            pattern_cutoff = datetime.now() - timedelta(days=pattern_ttl_days)
            await session.execute(
                update(Pattern)
                .where(Pattern.last_seen < pattern_cutoff)
                .values(is_active=False)
            )
            
            # Delete old analyses
            analysis_cutoff = datetime.now() - timedelta(days=analysis_ttl_days)
            await session.execute(
                delete(Analysis)
                .where(Analysis.timestamp < analysis_cutoff)
            )
            
            await session.commit()
