"""
LLM Integration Module for Salesforce Metadata Analysis
========================================================
Provides integration with various LLM providers (OpenAI, Azure OpenAI, Anthropic)
for intelligent analysis, documentation generation, and recommendations.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GITHUB = "github"
    LOCAL = "local"  # For local models like Ollama


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider
    api_key: Optional[str] = None
    model: str = "gpt-4"
    endpoint: Optional[str] = None  # For Azure OpenAI
    deployment_name: Optional[str] = None  # For Azure OpenAI
    temperature: float = 0.3
    max_tokens: int = 4000


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def analyze(self, prompt: str) -> str:
        """Send prompt to LLM and get response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize()
    
    def _initialize(self):
        try:
            from openai import OpenAI
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
        except ImportError:
            pass
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def analyze(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI client not available. Install openai package and set API key.")
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SALESFORCE_ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return response.choices[0].message.content


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI API client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize()
    
    def _initialize(self):
        try:
            from openai import AzureOpenAI
            api_key = self.config.api_key or os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = self.config.endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            
            if api_key and endpoint:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version="2024-02-01",
                    azure_endpoint=endpoint
                )
        except ImportError:
            pass
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def analyze(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError("Azure OpenAI client not available. Set API key and endpoint.")
        
        response = self.client.chat.completions.create(
            model=self.config.deployment_name or self.config.model,
            messages=[
                {"role": "system", "content": SALESFORCE_ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return response.choices[0].message.content


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self._initialize()
    
    def _initialize(self):
        try:
            import anthropic
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            pass
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def analyze(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError("Anthropic client not available. Install anthropic package and set API key.")
        
        response = self.client.messages.create(
            model=self.config.model if "claude" in self.config.model else "claude-3-sonnet-20240229",
            max_tokens=self.config.max_tokens,
            system=SALESFORCE_ANALYST_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text


class GitHubModelsClient(BaseLLMClient):
    """
    GitHub Models API client - FREE with GitHub Copilot Pro!
    Uses the Azure AI inference endpoint with GitHub token.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        self.token = None
        self.endpoint = "https://models.inference.ai.azure.com"
        self._initialize()
    
    def _initialize(self):
        """Initialize GitHub Models client"""
        self.token = self.config.api_key or os.getenv("GITHUB_TOKEN")
        if hasattr(self.config, 'endpoint') and self.config.endpoint:
            self.endpoint = self.config.endpoint
        
        if self.token:
            try:
                # GitHub Models uses the OpenAI-compatible API
                from openai import OpenAI
                self.client = OpenAI(
                    base_url=self.endpoint,
                    api_key=self.token
                )
            except ImportError:
                # Fallback to urllib if openai not installed
                self.client = "urllib"
    
    def is_available(self) -> bool:
        return self.token is not None and self.client is not None
    
    def analyze(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError("GitHub Models not available. Set GITHUB_TOKEN in .env file.")
        
        if self.client == "urllib":
            # Use urllib as fallback
            return self._analyze_urllib(prompt)
        
        # Use OpenAI client
        response = self.client.chat.completions.create(
            model=self.config.model or "gpt-4o",
            messages=[
                {"role": "system", "content": SALESFORCE_ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _analyze_urllib(self, prompt: str) -> str:
        """Fallback using urllib for GitHub Models API"""
        import urllib.request
        import urllib.error
        
        url = f"{self.endpoint}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        data = {
            "model": self.config.model or "gpt-4o",
            "messages": [
                {"role": "system", "content": SALESFORCE_ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise RuntimeError(f"GitHub Models API error: {e.code} - {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Connection error to GitHub Models ({self.endpoint}): {e.reason}\n"
                "This is likely blocked by your company firewall.\n"
                "Solution: Configure CUSTOM_LLM_* variables in .env to use your company's internal LLM."
            )


class CustomLLMClient(BaseLLMClient):
    """
    Custom/Internal LLM API client - Uses company's NLPBridge (llm_helper.py)
    
    When LLM_PROVIDER=custom, this directly calls the company's internal LLM
    via the NLPBridge class which handles authentication and API calls.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.bridge = None
        self._initialize()
    
    def _initialize(self):
        """Initialize using company's NLPBridge"""
        try:
            # Import the company's LLM helper
            import sys
            from pathlib import Path
            
            # Add project root to path if needed
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from llm_helper import NLPBridge
            self.bridge = NLPBridge
            print("✅ Custom LLM initialized using company NLPBridge")
        except ImportError as e:
            print(f"⚠️ Could not import llm_helper.py: {e}")
            self.bridge = None
        except Exception as e:
            print(f"⚠️ Error initializing NLPBridge: {e}")
            self.bridge = None
    
    def is_available(self) -> bool:
        return self.bridge is not None and self.bridge.enabled
    
    def analyze(self, prompt: str) -> str:
        """Send prompt to company's internal LLM via NLPBridge"""
        if not self.is_available():
            raise RuntimeError(
                "Custom LLM not available. Ensure llm_helper.py exists and NLPBridge.enabled=True"
            )
        
        # Build the full prompt with system context
        full_prompt = f"""{SALESFORCE_ANALYST_SYSTEM_PROMPT}

{prompt}"""
        
        try:
            response = self.bridge.ask_llm(full_prompt)
            return response
        except Exception as e:
            raise RuntimeError(f"Custom LLM API error: {e}")


# System prompt for Salesforce analysis
SALESFORCE_ANALYST_SYSTEM_PROMPT = """You are an expert Salesforce architect and developer with deep knowledge of:
- Salesforce Flows (Screen Flows, Record-Triggered Flows, Scheduled Flows, Platform Event Flows)
- Apex development and best practices
- Salesforce governor limits and performance optimization
- Security and sharing model
- Integration patterns
- DevOps and deployment strategies

When analyzing Salesforce metadata, you should:
1. Provide clear, business-friendly explanations
2. Identify potential issues (performance, security, maintainability)
3. Suggest optimizations and best practices
4. Consider governor limits implications
5. Recommend testing strategies
6. Identify dependencies and impact analysis

Format your responses in Markdown for readability."""


class MetadataPromptGenerator:
    """Generates specialized prompts for different analysis tasks"""
    
    @staticmethod
    def flow_analysis_prompt(flow_data: Dict) -> str:
        """Generate prompt for comprehensive flow analysis"""
        metadata = flow_data.get('Metadata', {})
        
        return f"""Analyze this Salesforce Flow metadata and provide a comprehensive assessment:

## Flow Metadata
```json
{json.dumps(metadata, indent=2, default=str)[:8000]}
```

Please provide:

### 1. Business Logic Summary
Explain what this flow does in business terms that a non-technical stakeholder would understand.

### 2. Technical Architecture
- Flow type and trigger mechanism
- Key decision points and branches
- Data operations (creates, updates, deletes)
- External integrations (Apex, Subflows)

### 3. Risk Assessment
- Governor limit concerns
- Error handling gaps
- Security considerations
- Data integrity risks

### 4. Best Practices Review
- What's done well
- Areas for improvement
- Recommended refactoring

### 5. Testing Recommendations
- Key scenarios to test
- Edge cases to consider
- Bulk testing requirements

### 6. Documentation
Generate technical documentation suitable for a developer handover."""

    @staticmethod
    def impact_analysis_prompt(flow_data: Dict, change_description: str) -> str:
        """Generate prompt for impact analysis"""
        metadata = flow_data.get('Metadata', {})
        
        return f"""Perform an impact analysis for a proposed change to this Salesforce Flow:

## Current Flow Metadata
```json
{json.dumps(metadata, indent=2, default=str)[:6000]}
```

## Proposed Change
{change_description}

Please analyze:

### 1. Direct Impacts
- Which flow elements will be affected?
- What data will be impacted?

### 2. Downstream Effects
- What other flows/processes depend on this?
- What integrations might be affected?

### 3. Risk Assessment
- What could break?
- Data integrity concerns
- User experience impacts

### 4. Testing Requirements
- What needs to be tested?
- Regression test scope

### 5. Rollback Plan
- How to revert if issues occur?

### 6. Recommendations
- Is this change advisable?
- Alternative approaches?"""

    @staticmethod
    def optimization_prompt(flow_data: Dict) -> str:
        """Generate prompt for optimization recommendations"""
        metadata = flow_data.get('Metadata', {})
        
        return f"""Review this Salesforce Flow for optimization opportunities:

## Flow Metadata
```json
{json.dumps(metadata, indent=2, default=str)[:8000]}
```

Please provide optimization recommendations for:

### 1. Performance
- Governor limit optimization
- Bulkification improvements
- Query optimization

### 2. Maintainability
- Code organization
- Naming conventions
- Documentation needs

### 3. Error Handling
- Fault path coverage
- Error notification improvements
- Recovery mechanisms

### 4. Security
- Data access patterns
- Field-level security
- Sharing rule considerations

### 5. Refactoring Suggestions
- Elements that could be simplified
- Opportunities for subflows
- Apex vs Flow trade-offs

Provide specific, actionable recommendations with examples where possible."""

    @staticmethod
    def documentation_prompt(flow_data: Dict) -> str:
        """Generate prompt for documentation generation"""
        metadata = flow_data.get('Metadata', {})
        
        return f"""Generate comprehensive documentation for this Salesforce Flow:

## Flow Metadata
```json
{json.dumps(metadata, indent=2, default=str)[:8000]}
```

Please create:

### 1. Executive Summary
A brief overview for business stakeholders (2-3 paragraphs).

### 2. Technical Specification
- Purpose and scope
- Trigger conditions
- Process flow diagram (in text/mermaid format)
- Input/Output specifications

### 3. Data Model
- Objects involved
- Fields read/written
- Record relationships

### 4. Integration Points
- Apex classes called
- External systems
- Subflows invoked

### 5. Error Handling
- Fault paths
- Notification mechanisms
- Recovery procedures

### 6. Testing Guide
- Test scenarios
- Expected outcomes
- Test data requirements

### 7. Maintenance Guide
- Common issues
- Troubleshooting steps
- Change procedures"""

    @staticmethod
    def security_review_prompt(flow_data: Dict) -> str:
        """Generate prompt for security review"""
        metadata = flow_data.get('Metadata', {})
        
        return f"""Perform a security review of this Salesforce Flow:

## Flow Metadata
```json
{json.dumps(metadata, indent=2, default=str)[:8000]}
```

Please assess:

### 1. Data Access
- What data is being accessed?
- Are there CRUD/FLS considerations?
- Sharing rule implications?

### 2. Run Context
- Does it run in system or user context?
- Privilege escalation concerns?

### 3. Input Validation
- Are inputs properly validated?
- Injection vulnerabilities?

### 4. Sensitive Data
- Is PII/sensitive data handled?
- Data exposure risks?

### 5. Audit Trail
- Are changes properly logged?
- Compliance considerations?

### 6. Recommendations
- Security improvements needed
- Best practices to implement"""


class LLMMetadataAnalyzer:
    """
    Main class for LLM-powered metadata analysis
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._default_config()
        self.client = self._create_client()
        self.prompt_generator = MetadataPromptGenerator()
    
    def _default_config(self) -> LLMConfig:
        """Create default configuration based on available environment variables"""
        # Check for Custom/Internal LLM first (company networks)
        if os.getenv("CUSTOM_LLM_API_KEY") and os.getenv("CUSTOM_LLM_BASE_URL"):
            return LLMConfig(
                provider=LLMProvider.LOCAL,  # Using LOCAL as custom
                model=os.getenv("CUSTOM_LLM_MODEL", "default"),
                api_key=os.getenv("CUSTOM_LLM_API_KEY"),
                endpoint=os.getenv("CUSTOM_LLM_BASE_URL")
            )
        elif os.getenv("AZURE_OPENAI_API_KEY"):
            return LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model="gpt-4",
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
            )
        elif os.getenv("GITHUB_TOKEN"):
            return LLMConfig(
                provider=LLMProvider.GITHUB, 
                model=os.getenv("GITHUB_MODEL", "gpt-4o"),
                api_key=os.getenv("GITHUB_TOKEN")
            )
        elif os.getenv("OPENAI_API_KEY"):
            return LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        elif os.getenv("ANTHROPIC_API_KEY"):
            return LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-sonnet-20240229")
        else:
            return LLMConfig(provider=LLMProvider.OPENAI)
    
    def _create_client(self) -> BaseLLMClient:
        """Create appropriate LLM client based on configuration"""
        if self.config.provider == LLMProvider.GITHUB:
            return GitHubModelsClient(self.config)
        elif self.config.provider == LLMProvider.OPENAI:
            return OpenAIClient(self.config)
        elif self.config.provider == LLMProvider.AZURE_OPENAI:
            return AzureOpenAIClient(self.config)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(self.config)
        elif self.config.provider == LLMProvider.LOCAL:
            # LOCAL is used for custom/internal APIs
            return CustomLLMClient(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def analyze(self, prompt: str) -> str:
        """Direct proxy to client analyze method for raw prompts"""
        return self.client.analyze(prompt)
    
    def analyze_flow(self, flow_data: Dict) -> str:
        """Perform comprehensive flow analysis"""
        prompt = self.prompt_generator.flow_analysis_prompt(flow_data)
        return self.client.analyze(prompt)
    
    def analyze_impact(self, flow_data: Dict, change_description: str) -> str:
        """Analyze impact of a proposed change"""
        prompt = self.prompt_generator.impact_analysis_prompt(flow_data, change_description)
        return self.client.analyze(prompt)
    
    def get_optimization_recommendations(self, flow_data: Dict) -> str:
        """Get optimization recommendations"""
        prompt = self.prompt_generator.optimization_prompt(flow_data)
        return self.client.analyze(prompt)
    
    def generate_documentation(self, flow_data: Dict) -> str:
        """Generate comprehensive documentation"""
        prompt = self.prompt_generator.documentation_prompt(flow_data)
        return self.client.analyze(prompt)
    
    def security_review(self, flow_data: Dict) -> str:
        """Perform security review"""
        prompt = self.prompt_generator.security_review_prompt(flow_data)
        return self.client.analyze(prompt)
    
    def custom_analysis(self, flow_data: Dict, custom_prompt: str) -> str:
        """Run custom analysis with user-provided prompt"""
        full_prompt = f"""Analyze this Salesforce Flow:

## Flow Metadata
```json
{json.dumps(flow_data.get('Metadata', {}), indent=2, default=str)[:8000]}
```

## Analysis Request
{custom_prompt}
"""
        return self.client.analyze(full_prompt)


def create_analyzer(
    provider: str = "auto",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMMetadataAnalyzer:
    """
    Factory function to create an LLM analyzer
    
    Args:
        provider: 'openai', 'azure', 'anthropic', 'github', 'custom', or 'auto' (detect from env)
        api_key: API key (optional, will use env vars if not provided)
        model: Model name (optional)
        **kwargs: Additional config options (e.g., endpoint for custom/azure)
        
    Returns:
        Configured LLMMetadataAnalyzer instance
    
    Usage:
        # Auto-detect from environment variables
        analyzer = create_analyzer()
        
        # Use specific provider
        analyzer = create_analyzer(provider='github')
        
        # Use custom/internal LLM
        analyzer = create_analyzer(
            provider='custom',
            api_key='your_api_key',
            model='your-model',
            endpoint='https://your-llm.internal.com/v1'
        )
    """
    provider_map = {
        'openai': LLMProvider.OPENAI,
        'azure': LLMProvider.AZURE_OPENAI,
        'azure_openai': LLMProvider.AZURE_OPENAI,
        'anthropic': LLMProvider.ANTHROPIC,
        'claude': LLMProvider.ANTHROPIC,
        'github': LLMProvider.GITHUB,
        'github_models': LLMProvider.GITHUB,
        'custom': LLMProvider.LOCAL,  # Custom/internal LLM
        'local': LLMProvider.LOCAL,
        'internal': LLMProvider.LOCAL
    }
    
    if provider == "auto" or provider not in provider_map:
        # Auto-detect based on environment
        config = None
    else:
        # Determine default model based on provider
        if model:
            default_model = model
        elif provider in ['github', 'github_models']:
            default_model = "gpt-4o"
        elif provider in ['custom', 'local', 'internal']:
            default_model = os.getenv("CUSTOM_LLM_MODEL", "default")
        elif provider in ['anthropic', 'claude']:
            default_model = "claude-3-sonnet-20240229"
        else:
            default_model = "gpt-4"
        
        config = LLMConfig(
            provider=provider_map[provider],
            api_key=api_key,
            model=default_model,
            **kwargs
        )
    
    return LLMMetadataAnalyzer(config)
