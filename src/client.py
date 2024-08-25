"""
Usage:
python client.py --api-spec-file ../openapi-specs/hivelocity.yaml
"""

import argparse
import os
from datetime import datetime, timedelta

from openai import OpenAI

parser = argparse.ArgumentParser()
parser.add_argument(
    "--api-spec-file",
    type=str,
    help="Path to the API specification file (absolute or relative)",
)
args = parser.parse_args()
api_spec_file_path = args.api_spec_file if args.api_spec_file else "hivelocity.yaml"
api_spec_file_path = os.path.abspath(api_spec_file_path)
compliance_standards = "GDPR, SOC2"
model_url = "https://services.komodo.io/skqse3sptzoc5gre2zlf5yk/v1"
model_name = "meta-llama/Meta-Llama-3.1-8B-Instruct"
temp = 0.3
# stop_token_ids = "128009,128001"

# Set OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = model_url
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

# model_name = "gpt-4o"
# chatgpt_api_key = ""
# client = OpenAI(api_key=chatgpt_api_key)

system_message = """
**Prompt:**

You are an API governance AI agent. Your task is to generate a single YAML file based on the provided OpenAPI specification and compliance requirements. The output should consist only of the YAML file with a top-level `rules` array. No additional text or explanations should be included in the output, just the complete YAML file.

Ensure that the rules cover a broad range of aspects, including but not limited to security, compliance, performance, consistency, and documentation. The rules should be checking the standard OpenAPI spec fields, do not add any additional fields that are not standard OpenAPI spec fields.

**Task Overview:**
1. **Industry Inference**: Accurately infer the industry based on the structure, endpoints, data types, and other relevant elements in the OpenAPI specification.
2. **Rule Generation**: Create specific governance rules focused on security, compliance, and industry standards. Ensure these rules are relevant to the inferred industry and adhere to the provided compliance requirements. You should both apply the base rules and generate additional industry-specific rules.
3. **Rule Format**:
    - Each rule must be structured in YAML format with the following elements:
        - `id`: A unique identifier for the rule.
        - `description`: A brief explanation of the rule's purpose.
        - `conditions`: A list of conditions that must be met in the OpenAPI spec for the rule to apply.
        - `fix`: A section detailing how to fix the issue if the conditions are not met, including a code snippet.
4. **Output Requirements**: The output should consist only of the YAML file with a top-level `rules` array that includes all the relevant rules. No additional text or explanations should be included in the output, just the complete YAML file.

**Base Rules:**
```yaml
rules:
  # Security Rules
  - id: "SEC002"
    description: "Ensure all protected endpoints include OAuth scopes."
    conditions:
      - "openapi.paths[*].security.OAuth2 exists"
      - "openapi.paths[*].security.OAuth2[*].scopes exists"
    fix:
      description: "Add appropriate OAuth scopes to the security definition."
      fix_snippet:
        security:
          - OAuth2:
              scopes:
                write: "Allows writing to the resource."
                read: "Allows reading from the resource."

  - id: "SEC003"
    description: "Ensure all production endpoints are served over HTTPS."
    conditions:
      - "openapi.servers[*].url.startswith('https://')"
    fix:
      description: "Update server URLs to enforce HTTPS."
      fix_snippet:
        servers:
          - url: "https://example.com/api"

  - id: "SEC004"
    description: "Ensure security schemes are defined for all public endpoints."
    conditions:
      - "openapi.paths[*].security exists"
    fix:
      description: "Add security schemes such as OAuth2 or API Key."
      fix_snippet:
        security:
          - OAuth2:
              flows:
                implicit:
                  authorizationUrl: "https://example.com/oauth/authorize"
                  scopes:
                    read: "Grants read access"
                    write: "Grants write access"

  # Performance and Rate Limiting Rules
  - id: "PERF001"
    description: "Ensure rate limiting is enforced on all public APIs."
    conditions:
      - "openapi.paths[*].responses.200.headers.X-RateLimit-Limit exists"
      - "openapi.paths[*].responses.200.headers.X-RateLimit-Remaining exists"
      - "openapi.paths[*].responses.200.headers.X-RateLimit-Reset exists"
    fix:
      description: "Add rate limiting headers to the response definitions."
      fix_snippet:
        responses:
          200:
            headers:
              X-RateLimit-Limit:
                schema:
                  type: integer
              X-RateLimit-Remaining:
                schema:
                  type: integer
              X-RateLimit-Reset:
                schema:
                  type: integer

  - id: "PERF002"
    description: "Ensure caching headers are applied to improve performance."
    conditions:
      - "openapi.paths[*].responses.200.headers.Cache-Control exists"
    fix:
      description: "Add Cache-Control headers to responses."
      fix_snippet:
        responses:
          200:
            headers:
              Cache-Control:
                schema:
                  type: string
                  description: "Caching directive for improving performance."

  # Privacy and Data Compliance Rules
  - id: "PRIV001"
    description: "Ensure sensitive data is masked or encrypted."
    conditions:
      - "openapi.paths[*].responses[*].content.application/json.schema.properties.credit_card_number exists"
    fix:
      description: "Mask or encrypt sensitive fields in the response."
      fix_snippet:
        responses:
          200:
            content:
              application/json:
                schema:
                  properties:
                    credit_card_number:
                      type: string
                      description: "Encrypted or masked credit card number."

  - id: "PRIV002"
    description: "Ensure compliance with GDPR/CCPA by handling PII correctly."
    conditions:
      - "openapi.paths[*].responses[*].content.application/json.schema.properties.email exists"
      - "openapi.paths[*].responses[*].content.application/json.schema.properties.phone_number exists"
    fix:
      description: "Ensure PII is handled securely and consider anonymization where possible."
      fix_snippet:
        properties:
          email:
            type: string
            format: email
            description: "User email, ensure encrypted or anonymized if required."
          phone_number:
            type: string
            description: "User phone number, ensure encrypted or anonymized if required."

  # Consistency Rules
  - id: "CONSIST001"
    description: "Ensure all endpoints and properties follow consistent naming conventions."
    conditions:
      - "openapi.paths[*].parameters[*].name matches '^([a-z]+_)*[a-z]+$'"  # Example for snake_case

  - id: "CONSIST002"
    description: "Ensure consistent naming for parameters and properties using camelCase."
    conditions:
      - "openapi.components.schemas[*].properties[*].name matches '^[a-z][a-zA-Z0-9]*$'"  # Example for camelCase

  # Deprecation and Versioning Rules
  - id: "DEP001"
    description: "Ensure deprecated endpoints are marked and documented with alternatives."
    conditions:
      - "openapi.paths[*].deprecated exists"
      - "openapi.paths[*].description contains 'Use the following alternative:'"
    fix:
      description: "Mark the endpoint as deprecated and provide an alternative."
      fix_snippet:
        deprecated: true
        description: "This endpoint is deprecated. Use /v2/transactions. This endpoint will be sunset on 2024-12-31."

  - id: "VER001"
    description: "Ensure all APIs have versioning in their paths."
    conditions:
      - "openapi.paths[*] matches '^/v[0-9]+/.*'"
    fix:
      description: "Add versioning to the path."
      fix_snippet:
        paths:
          /v1/resource:
            get:
              summary: "This is an example of versioned API path."

  # Documentation Completeness
  - id: "DOC001"
    description: "Ensure all operations have a description."
    conditions:
      - "openapi.paths[*][*].description exists"
    fix:
      description: "Add descriptions to operations."
      fix_snippet:
        description: "This is a placeholder description for the operation."

  - id: "OP_ID001"
    description: "Ensure all operations have unique operation IDs."
    conditions:
      - "openapi.paths[*][*].operationId exists"
    fix:
      description: "Add unique operation IDs."
      fix_snippet:
        operationId: "placeholderOperationId"

  # Path Parameter Validation
  - id: "PARAM001"
    description: "Ensure all path parameters are defined in components or inline."
    conditions:
      - "openapi.paths[*].parameters[*].in == 'path'"
      - "openapi.components.parameters[*].in == 'path'"
    fix:
      description: "Define missing path parameters."
      fix_snippet:
        parameters:
          - name: "parameterName"
            in: "path"
            required: true
            schema:
              type: "string"

  # Response Structure Validation
  - id: "RESP001"
    description: "Ensure all responses include a content type."
    conditions:
      - "openapi.paths[*].responses[*].content exists"
    fix:
      description: "Add default content type to responses."
      fix_snippet:
        content:
          application/json:
            schema:
              type: object

  # Server Validation
  - id: "SERVER001"
    description: "Ensure server URLs are valid and not set to localhost or example.com."
    conditions:
      - "!openapi.servers[*].url contains 'localhost'"
      - "!openapi.servers[*].url contains 'example.com'"
    fix:
      description: "Replace placeholder server URLs with production URLs."
      fix_snippet:
        servers:
          - url: "https://api.yourdomain.com"
"""


api_spec_file_str = ""
with open(api_spec_file_path, "r") as f:
    api_spec_file_str = f.read()

print(f"Loaded API spec from {api_spec_file_path}")

user_message = f"""
I require the {compliance_standards} compliance standards. Here's my API spec:
{api_spec_file_str}
"""

print(f"Assembled user message, compliances: {compliance_standards}")

messages = [
    {"role": "system", "content": system_message},
    {"role": "user", "content": user_message},
]

t_one = datetime.now()
completion = client.chat.completions.create(
    model=model_name,
    messages=messages,
    temperature=temp,
    stream=False,
)
t_two = datetime.now()

duration = t_two - t_one

response_content = completion.choices[0].message.content
usage = completion.usage

print(completion.choices[0].message.content)

print(
    f"Tokens - prompt {usage.prompt_tokens}, completion {usage.completion_tokens}, total {usage.total_tokens}"
)
print(f"Duration: {duration.seconds} seconds")
