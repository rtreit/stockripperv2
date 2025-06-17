"""
Shared configuration and utilities for A2A agents
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import structlog


class Settings(BaseSettings):
    """Pydantic v2 Settings for environment configuration"""
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    # LLM API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI Model")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API Key")
      # Agent URLs
    market_analyst_url: str = Field(default="http://localhost:8001", description="Market Analyst URL")
    planner_url: str = Field(default="http://localhost:8002", description="Planner URL") 
    mailer_url: str = Field(default="http://localhost:8003", description="Mailer URL")
    
    # Registry
    a2a_registry_url: str = Field(default="http://localhost:8000", description="A2A Registry URL")
      # Alpaca Trading (for stdio MCP servers)
    alpaca_api_key: Optional[str] = Field(default=None, description="Alpaca API Key")
    alpaca_secret_key: Optional[str] = Field(default=None, description="Alpaca Secret Key")
    alpaca_base_url: str = Field(default="https://paper-api.alpaca.markets", description="Alpaca Base URL")
    paper: Optional[str] = Field(default="True", description="Alpaca Paper Trading Mode")
    
    # Gmail (for stdio MCP servers)
    gmail_client_id: Optional[str] = Field(default=None, description="Gmail Client ID")
    gmail_client_secret: Optional[str] = Field(default=None, description="Gmail Client Secret")
    gmail_credentials_path: str = Field(default="./credentials/gmail_credentials.json", description="Gmail Credentials Path")
    gmail_token_path: str = Field(default="./credentials/gmail_token.json", description="Gmail Token Path")
    google_application_credentials: Optional[str] = Field(default=None, description="Google Application Credentials Path")
    default_email_recipient: str = Field(default="admin@stockripper.com", description="Default Email Recipient")
    email_cc_recipients: Optional[str] = Field(default=None, description="Email CC Recipients (comma-separated)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log Level")
    log_format: str = Field(default="json", description="Log Format")
    x_correlation_id_header: str = Field(default="X-Correlation-ID", description="X-Correlation-ID Header")


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


def setup_logging(settings: Settings) -> None:
    """Setup structured logging with correlation ID"""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Global settings instance
settings = get_settings()

# Setup logging
setup_logging(settings)

# Global logger instance  
logger = structlog.get_logger()


# Contains AI-generated edits.
