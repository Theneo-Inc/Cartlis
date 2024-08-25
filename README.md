
# Cartlis: AI-Powered API Governance Agent

Cartlis is an AI-powered API governance tool that enforces API governance rules in real-time. It integrates seamlessly with your infrastructure, automatically patching violations to ensure compliance, security, and performance across your APIs.

## Key Features
- **Real-time API Governance**: Automatically enforces governance rules for your API.
- **Auto-Patching**: Identifies and fixes violations related to compliance, security, and performance.
- **Customizable Rulesets**: Generates rulesets tailored to your industry and compliance requirements.

## Flow Overview
1. **Input**: Cartlis takes your API specification (in OpenAPI format) as input.
2. **Processing**: Cartlis applies industry-standard governance rules and validates your API.
3. **Output**: Generates a report of violations and fixes them automatically or provides guidance on what to correct manually.
4. **Continuous Improvement**: Enforces ongoing governance with real-time monitoring and auto-patching.

## Setup and Installation

### 1. Installation
You can install Cartlis using pip:

```bash
pip install -e .
```

This will install the Cartlis CLI tool.

### 2. Define Environment Variables
To get started, you will need to define some environment variables that describe your API and the governance rules to enforce. These environment variables should be added to your `.env` file in the root directory of your project.

```bash
# .env file example

API_DESCRIPTION="Public facing API used by external developers"
API_USER_BASE="Developers in the financial sector"
API_COMPLIANCE="GDPR, SOC2"
GOVERNANCE_SCOPES="Security, Performance, Compliance"
```

Make sure your `.env` file includes details about your API, such as:
- Whether it's a public or private API
- The intended user base (e.g., developers, internal teams)
- Applicable compliance standards (e.g., GDPR, SOC2)

### 3. Running Cartlis
To run Cartlis against your API specification, use the following command:

```bash
cartlis --spec path/to/your/api_spec.yaml
```

This will validate your API spec, apply governance rules, and provide a report of violations and fixes.

## Usage

Cartlis is designed to work with OpenAPI specifications. Here’s a basic example of how to use the tool:

```bash
cartlis --spec api_spec.yaml
```

Cartlis will output a list of detected violations and automatically apply fixes wherever possible. For example:
- Adding missing OAuth2 scopes
- Enforcing rate limiting headers
- Adding caching headers to improve performance
- Ensuring consistent naming conventions

### Example Output

```
Applying fix for violation: SEC002 at PUT /pet
Added OAuth2 scopes to PUT /pet
Added default description to requestBody in PUT /pet
Fixing None response for status code 404 in PUT /pet
...
All fixes have been applied and saved to fixed_api_spec.yaml
```

### Auto-Patching Capabilities
Cartlis will automatically attempt to patch violations in your API specification, such as:
- Missing security definitions
- Inconsistent parameter names
- Lack of versioning in paths
- Missing response content types

## Contribution Guidelines
Contributions are welcome! Please ensure you follow our coding standards and best practices. Submit pull requests with clear descriptions of changes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.