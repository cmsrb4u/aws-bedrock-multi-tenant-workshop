"""Configuration for AWS Bedrock lab exercises."""

# AWS Region configuration
Region = "us-west-2"

# Model IDs for Anthropic Claude models on Bedrock
class ModelId:
    """Claude model IDs available on AWS Bedrock."""

    # Claude 4.x models
    CLAUDE_OPUS_4_6 = "anthropic.claude-opus-4-6-v1"
    CLAUDE_OPUS_4_5 = "anthropic.claude-opus-4-5-20251101-v1:0"
    CLAUDE_OPUS_4_1 = "anthropic.claude-opus-4-1-20250805-v1:0"
    CLAUDE_OPUS_4 = "anthropic.claude-opus-4-20250514-v1:0"

    CLAUDE_SONNET_4_6 = "anthropic.claude-sonnet-4-6"
    CLAUDE_SONNET_4_5 = "anthropic.claude-sonnet-4-5-20250929-v1:0"
    CLAUDE_SONNET_4 = "anthropic.claude-sonnet-4-20250514-v1:0"

    CLAUDE_HAIKU_4_5 = "anthropic.claude-haiku-4-5-20251001-v1:0"

    # Claude 3.x models
    CLAUDE_3_7_SONNET = "anthropic.claude-3-7-sonnet-20250219-v1:0"
    CLAUDE_3_5_SONNET_V2 = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    CLAUDE_3_5_HAIKU = "anthropic.claude-3-5-haiku-20241022-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"

    # Default model (using inference profile for on-demand throughput)
    DEFAULT = "us.anthropic.claude-sonnet-4-6"  # System inference profile


# Sample prompts for testing
class Prompt:
    """Sample prompts for Bedrock API testing."""

    SIMPLE = "Hello! How are you today?"

    EXPLAIN_AI = "Explain artificial intelligence in simple terms."

    CODE_EXAMPLE = "Write a Python function to calculate the fibonacci sequence."

    SUMMARIZE = """Please summarize the following text:
Amazon Bedrock is a fully managed service that offers a choice of high-performing
foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere,
Meta, Mistral AI, Stability AI, and Amazon through a single API, along with a broad
set of capabilities you need to build generative AI applications with security,
privacy, and responsible AI."""

    JSON_OUTPUT = """Generate a JSON object with information about three programming languages.
Each language should have: name, year_created, and primary_use fields."""

    CREATIVE = "Write a haiku about cloud computing."

    # Default prompt
    DEFAULT = SIMPLE


# Inference configuration defaults
class InferenceConfig:
    """Default inference configuration parameters."""

    MAX_TOKENS = 2048
    TEMPERATURE = 1.0
    TOP_P = 0.999
    TOP_K = 250

    @classmethod
    def get_default_config(cls):
        """Return default inference configuration."""
        return {
            "maxTokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "topP": cls.TOP_P
        }


# Tenant-specific tags for Application Inference Profiles
tenant_a_tags = [
    {"key": "tenant", "value": "tenant_a"},
    {"key": "department", "value": "marketing"},
    {"key": "costcenter", "value": "marketing-ops"}
]

tenant_b_tags = [
    {"key": "tenant", "value": "tenant_b"},
    {"key": "department", "value": "sales"},
    {"key": "costcenter", "value": "sales-ops"}
]
