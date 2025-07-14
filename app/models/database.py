"""SQLAlchemy models for the build analyzer database."""
from datetime import datetime
import json
from typing import Optional, Dict, Any, List
import sqlalchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.models.build import BuildInfo, BuildAnalysis

Base = declarative_base()

class Build(Base):
    """Build information table."""
    __tablename__ = "builds"
    
    id = Column(Integer, primary_key=True)
    job_name = Column(String, nullable=False, index=True)
    build_number = Column(Integer, nullable=False)
    result = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    duration = Column(Integer)
    parameters = Column(JSON)
    url = Column(String)
    console_log = Column(Text)
    
    # One-to-one relationship with Analysis, using build_id as the primary relationship
    analysis = relationship(
        "Analysis",
        back_populates="build",
        uselist=False,
        foreign_keys="Analysis.build_id",
        cascade="all, delete-orphan"
    )
    
    # Builds that reference this build as their last successful build
    referenced_analyses = relationship(
        "Analysis",
        foreign_keys="Analysis.last_success_id",
        backref="last_success",
        overlaps="analysis"
    )
    
    __table_args__ = (
        UniqueConstraint('job_name', 'build_number', name='uix_build_job_number'),
        {'extend_existing': True}
    )
    
    @classmethod
    def from_build_info(cls, build_info: BuildInfo) -> "Build":
        """Create a Build record from a BuildInfo object."""
        return cls(
            job_name=build_info.job_name,
            build_number=build_info.build_number,
            result=build_info.result,
            timestamp=build_info.timestamp,
            duration=build_info.duration,
            parameters=build_info.parameters,
            url=build_info.url,
            console_log=build_info.console_log
        )

class Analysis(Base):
    """Build analysis results table."""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True)
    build_id = Column(Integer, ForeignKey("builds.id"), nullable=False, unique=True)
    last_success_id = Column(Integer, ForeignKey("builds.id"), nullable=True)
    error_patterns = Column(JSON, nullable=False, default=list)
    differences = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Primary relationship with the analyzed build
    build = relationship(
        "Build",
        foreign_keys=[build_id],
        back_populates="analysis"
    )
    
    @classmethod
    def from_build_analysis(cls, analysis: BuildAnalysis, build_id: int, 
                          last_success_id: Optional[int] = None) -> "Analysis":
        """Create an Analysis record from a BuildAnalysis object."""
        return cls(
            build_id=build_id,
            last_success_id=last_success_id,
            error_patterns=analysis.error_patterns,
            differences=analysis.differences,
            recommendations=analysis.recommendations,
            severity=analysis.severity,
            confidence=analysis.confidence,
            timestamp=analysis.timestamp
        )

class Pattern(Base):
    """Learned build failure patterns table."""
    __tablename__ = "patterns"
    
    id = Column(Integer, primary_key=True)
    job_name = Column(String, nullable=False, index=True)
    pattern = Column(String, nullable=False)
    frequency = Column(Integer, nullable=False, default=1)
    last_seen = Column(DateTime, nullable=False)
    solution = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    @classmethod
    def from_dict(cls, job_name: str, pattern_dict: Dict[str, Any]) -> "Pattern":
        """Create a Pattern record from a dictionary."""
        return cls(
            job_name=job_name,
            pattern=pattern_dict['pattern'],
            frequency=pattern_dict['frequency'],
            last_seen=pattern_dict['last_seen'],
            solution=pattern_dict.get('solution')
        )

class Action(Base):
    """Agent action history table."""
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True)
    build_id = Column(Integer, ForeignKey("builds.id"), nullable=False)
    type = Column(String, nullable=False)
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)
    result = Column(String)
    timestamp = Column(DateTime, nullable=False)
    
    build = relationship("Build")
    pattern = relationship("Pattern")
    
    @classmethod
    def from_dict(cls, build_id: int, action_dict: Dict[str, Any], 
                 pattern_id: Optional[int] = None) -> "Action":
        """Create an Action record from a dictionary."""
        return cls(
            build_id=build_id,
            type=action_dict['type'],
            pattern_id=pattern_id,
            result=action_dict['result'],
            timestamp=datetime.fromisoformat(action_dict['timestamp'])
        )
