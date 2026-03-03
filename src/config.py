"""
Configuration Module
====================
Loads environment variables from .env file and provides configuration
for LLM providers and Salesforce connections.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum


def load_env_file(env_path: str = None):
    """
    Load environment variables from .env file
    
    Args:
        env_path: Path to .env file. If None, searches in current dir and parent dirs.
    """
    # Try to use python-dotenv if available
    try:
        from dotenv import load_dotenv
        
        if env_path:
            load_dotenv(env_path)
        else:
            # Search for .env file starting from script location
            try:
                current = Path.cwd()
            except (FileNotFoundError, OSError):
                # Fallback to script directory
                current = Path(__file__).parent.parent
            
            for _ in range(5):  # Search up to 5 levels
                env_file = current / '.env'
                if env_file.exists():
                    load_dotenv(env_file)
                    print(f"✓ Loaded configuration from: {env_file}")
                    return True
                current = current.parent
            
            # Try default location
            load_dotenv()
        return True
        
    except ImportError:
        # Manual loading if dotenv not installed
        if env_path is None:
            try:
                current = Path.cwd()
            except (FileNotFoundError, OSError):
                # Fallback to script directory
                current = Path(__file__).parent.parent
            
            for _ in range(5):
                env_file = current / '.env'
                if env_file.exists():
                    env_path = str(env_file)
                    break
                current = current.parent
        
        if env_path and Path(env_path).exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if value:  # Only set if value is not empty
                            os.environ[key] = value
            print(f"✓ Loaded configuration from: {env_path}")
            return True
        
        return False


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure"
    ANTHROPIC = "anthropic"
    GITHUB = "github"
    OLLAMA = "ollama"
    AUTO = "auto"


@dataclass
class GitHubModelsConfig:
    """GitHub Models configuration (free with Copilot Pro!)"""
    token: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4000
    endpoint: str = "https://models.inference.ai.azure.com"
    
    @classmethod
    def from_env(cls) -> 'GitHubModelsConfig':
        return cls(
            token=os.getenv("GITHUB_TOKEN", ""),
            model=os.getenv("GITHUB_MODEL", "gpt-4o"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
            endpoint=os.getenv("GITHUB_MODELS_ENDPOINT", "https://models.inference.ai.azure.com")
        )
    
    def is_configured(self) -> bool:
        return bool(self.token)


@dataclass
class OpenAIConfig:
    """OpenAI configuration"""
    api_key: str = ""
    model: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 4000
    
    @classmethod
    def from_env(cls) -> 'OpenAIConfig':
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000"))
        )
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI configuration"""
    api_key: str = ""
    endpoint: str = ""
    deployment: str = ""
    api_version: str = "2024-02-01"
    temperature: float = 0.3
    max_tokens: int = 4000
    
    @classmethod
    def from_env(cls) -> 'AzureOpenAIConfig':
        return cls(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000"))
        )
    
    def is_configured(self) -> bool:
        return bool(self.api_key and self.endpoint and self.deployment)


@dataclass
class AnthropicConfig:
    """Anthropic Claude configuration"""
    api_key: str = ""
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.3
    max_tokens: int = 4000
    
    @classmethod
    def from_env(cls) -> 'AnthropicConfig':
        return cls(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000"))
        )
    
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class OllamaConfig:
    """Ollama (local LLM) configuration"""
    host: str = "http://localhost:11434"
    model: str = "llama2"
    
    @classmethod
    def from_env(cls) -> 'OllamaConfig':
        return cls(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama2")
        )


@dataclass
class SalesforceConfig:
    """Salesforce connection configuration"""
    # OAuth credentials
    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    password: str = ""
    security_token: str = ""
    
    # Direct access
    access_token: str = ""
    instance_url: str = ""
    
    # Settings
    api_version: str = "59.0"
    is_sandbox: bool = False
    
    @classmethod
    def from_env(cls) -> 'SalesforceConfig':
        return cls(
            client_id=os.getenv("SF_CLIENT_ID", ""),
            client_secret=os.getenv("SF_CLIENT_SECRET", ""),
            username=os.getenv("SF_USERNAME", ""),
            password=os.getenv("SF_PASSWORD", ""),
            security_token=os.getenv("SF_SECURITY_TOKEN", ""),
            access_token=os.getenv("SF_ACCESS_TOKEN", ""),
            instance_url=os.getenv("SF_INSTANCE_URL", ""),
            api_version=os.getenv("SF_API_VERSION", "59.0"),
            is_sandbox=os.getenv("SF_IS_SANDBOX", "false").lower() == "true"
        )
    
    def has_oauth_credentials(self) -> bool:
        """Check if OAuth credentials are configured"""
        return bool(self.client_id and self.client_secret and self.username)
    
    def has_direct_access(self) -> bool:
        """Check if direct access token is configured"""
        return bool(self.access_token and self.instance_url)
    
    def is_configured(self) -> bool:
        """Check if any valid configuration exists"""
        return self.has_oauth_credentials() or self.has_direct_access()


@dataclass
class AppConfig:
    """Application configuration"""
    log_level: str = "INFO"
    output_format: str = "markdown"
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            output_format=os.getenv("OUTPUT_FORMAT", "markdown"),
            cache_enabled=os.getenv("ANALYSIS_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("ANALYSIS_CACHE_TTL", "3600"))
        )


@dataclass
class Config:
    """
    Main configuration class that aggregates all configurations
    """
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    azure_openai: AzureOpenAIConfig = field(default_factory=AzureOpenAIConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    github: GitHubModelsConfig = field(default_factory=GitHubModelsConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    salesforce: SalesforceConfig = field(default_factory=SalesforceConfig)
    app: AppConfig = field(default_factory=AppConfig)
    llm_provider: str = "auto"
    
    @classmethod
    def load(cls, env_path: str = None) -> 'Config':
        """
        Load configuration from environment variables
        
        Args:
            env_path: Optional path to .env file
            
        Returns:
            Configured Config instance
        """
        # Load .env file
        load_env_file(env_path)
        
        return cls(
            openai=OpenAIConfig.from_env(),
            azure_openai=AzureOpenAIConfig.from_env(),
            anthropic=AnthropicConfig.from_env(),
            github=GitHubModelsConfig.from_env(),
            ollama=OllamaConfig.from_env(),
            salesforce=SalesforceConfig.from_env(),
            app=AppConfig.from_env(),
            llm_provider=os.getenv("LLM_PROVIDER", "auto")
        )
    
    def get_active_llm_provider(self) -> Optional[LLMProvider]:
        """
        Determine which LLM provider to use based on configuration
        
        Returns:
            LLMProvider enum or None if no provider is configured
        """
        if self.llm_provider == "auto":
            # Auto-detect based on available credentials
            if self.github.is_configured():
                return LLMProvider.GITHUB
            elif self.openai.is_configured():
                return LLMProvider.OPENAI
            elif self.azure_openai.is_configured():
                return LLMProvider.AZURE_OPENAI
            elif self.anthropic.is_configured():
                return LLMProvider.ANTHROPIC
            else:
                return None
        else:
            provider_map = {
                "openai": LLMProvider.OPENAI,
                "azure": LLMProvider.AZURE_OPENAI,
                "anthropic": LLMProvider.ANTHROPIC,
                "github": LLMProvider.GITHUB,
                "ollama": LLMProvider.OLLAMA
            }
            return provider_map.get(self.llm_provider.lower())
    
    def get_llm_config(self) -> Optional[Dict[str, Any]]:
        """
        Get configuration for the active LLM provider
        
        Returns:
            Dictionary with LLM configuration
        """
        provider = self.get_active_llm_provider()
        
        if provider == LLMProvider.GITHUB:
            return {
                "provider": "github",
                "token": self.github.token,
                "model": self.github.model,
                "endpoint": self.github.endpoint,
                "temperature": self.github.temperature,
                "max_tokens": self.github.max_tokens
            }
        elif provider == LLMProvider.OPENAI:
            return {
                "provider": "openai",
                "api_key": self.openai.api_key,
                "model": self.openai.model,
                "temperature": self.openai.temperature,
                "max_tokens": self.openai.max_tokens
            }
        elif provider == LLMProvider.AZURE_OPENAI:
            return {
                "provider": "azure",
                "api_key": self.azure_openai.api_key,
                "endpoint": self.azure_openai.endpoint,
                "deployment_name": self.azure_openai.deployment,
                "api_version": self.azure_openai.api_version,
                "temperature": self.azure_openai.temperature,
                "max_tokens": self.azure_openai.max_tokens
            }
        elif provider == LLMProvider.ANTHROPIC:
            return {
                "provider": "anthropic",
                "api_key": self.anthropic.api_key,
                "model": self.anthropic.model,
                "temperature": self.anthropic.temperature,
                "max_tokens": self.anthropic.max_tokens
            }
        
        return None
    
    def print_status(self):
        """Print configuration status"""
        print("\n" + "=" * 50)
        print("Configuration Status")
        print("=" * 50)
        
        # LLM Status
        print("\n📦 LLM Providers:")
        print(f"   GitHub Models: {'✅ Configured (FREE with Copilot Pro!)' if self.github.is_configured() else '❌ Not configured'}")
        print(f"   OpenAI:        {'✅ Configured' if self.openai.is_configured() else '❌ Not configured'}")
        print(f"   Azure OpenAI:  {'✅ Configured' if self.azure_openai.is_configured() else '❌ Not configured'}")
        print(f"   Anthropic:     {'✅ Configured' if self.anthropic.is_configured() else '❌ Not configured'}")
        
        active = self.get_active_llm_provider()
        if active:
            print(f"\n   🎯 Active Provider: {active.value}")
            if active == LLMProvider.GITHUB:
                print(f"   🤖 Model: {self.github.model}")
        else:
            print(f"\n   ⚠️  No LLM provider configured (rule-based mode)")
        
        # Salesforce Status
        print("\n☁️  Salesforce:")
        if self.salesforce.has_direct_access():
            print(f"   ✅ Direct Access Token configured")
            print(f"   Instance: {self.salesforce.instance_url}")
        elif self.salesforce.has_oauth_credentials():
            print(f"   ✅ OAuth credentials configured")
            print(f"   Username: {self.salesforce.username}")
        else:
            print(f"   ❌ Not configured")
        
        print(f"   API Version: {self.salesforce.api_version}")
        
        # App Settings
        print("\n⚙️  Settings:")
        print(f"   Log Level: {self.app.log_level}")
        print(f"   Output Format: {self.app.output_format}")
        print(f"   Cache: {'Enabled' if self.app.cache_enabled else 'Disabled'}")
        
        print("\n" + "=" * 50)


# Global config instance
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get the global configuration instance
    
    Args:
        reload: If True, reload configuration from environment
        
    Returns:
        Config instance
    """
    global _config
    
    if _config is None or reload:
        _config = Config.load()
    
    return _config


def init_config(env_path: str = None) -> Config:
    """
    Initialize configuration from a specific .env file
    
    Args:
        env_path: Path to .env file
        
    Returns:
        Config instance
    """
    global _config
    _config = Config.load(env_path)
    return _config


# =============================================================================
# CLI for testing configuration
# =============================================================================

if __name__ == "__main__":
    print("Loading configuration...")
    config = get_config()
    config.print_status()
    
    # Test LLM config
    llm_config = config.get_llm_config()
    if llm_config:
        print(f"\nLLM Config: {llm_config['provider']}")
        print(f"Model: {llm_config.get('model', llm_config.get('deployment_name', 'N/A'))}")
