import yaml
import sys
from .fixer import fix_spec
import re


# Load rules from YAML
def load_rules(rule_file):
    with open(rule_file, 'r') as file:
        rules = yaml.safe_load(file)
    return rules

# Validate the API spec against governance rules
def validate_spec(api_spec, rules):
    violations = []

    for rule in rules['rules']:
        # SEC002: Ensure all protected endpoints include OAuth scopes
        if rule['id'] == 'SEC002':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    if 'security' not in details or 'OAuth2' not in details.get('security', [{}])[0]:
                        violations.append({
                            'id': rule['id'],
                            'description': f"{rule['description']} at {method.upper()} {path}",
                            'fix': rule.get('fix'),
                            'path': path,
                            'method': method
                        })

        # SEC004: Ensure security schemes are defined for all public endpoints
        elif rule['id'] == 'SEC004':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    if 'security' not in details:
                        violations.append({
                            'id': rule['id'],
                            'description': f"{rule['description']} at {method.upper()} {path}",
                            'fix': rule.get('fix'),
                            'path': path,
                            'method': method
                        })

        # PERF001: Ensure rate limiting is enforced on all public APIs
        elif rule['id'] == 'PERF001':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    if 'responses' in details and '200' in details['responses']:
                        headers = details['responses']['200'].get('headers', {})
                        if 'X-RateLimit-Limit' not in headers or 'X-RateLimit-Remaining' not in headers or 'X-RateLimit-Reset' not in headers:
                            violations.append({
                                'id': rule['id'],
                                'description': f"{rule['description']} at {method.upper()} {path}",
                                'fix': rule.get('fix'),
                                'path': path,
                                'method': method
                            })

        # PERF002: Ensure caching headers are applied to improve performance
        elif rule['id'] == 'PERF002':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    if 'responses' in details and '200' in details['responses']:
                        headers = details['responses']['200'].get('headers', {})
                        if 'Cache-Control' not in headers:
                            violations.append({
                                'id': rule['id'],
                                'description': f"{rule['description']} at {method.upper()} {path}",
                                'fix': rule.get('fix'),
                                'path': path,
                                'method': method
                            })

        # CONSIST001: Ensure all endpoints and properties follow consistent naming conventions (snake_case)
        elif rule['id'] == 'CONSIST001':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    for param in details.get('parameters', []):
                        if 'name' in param and not re.match('^([a-z]+_)*[a-z]+$', param['name']):
                            violations.append({
                                'id': rule['id'],
                                'description': f"Parameter '{param['name']}' does not follow naming convention at {method.upper()} {path}",
                                'fix': rule.get('fix'),
                                'path': path,
                                'method': method
                            })

        # VER001: Ensure all APIs have versioning in their paths
        elif rule['id'] == 'VER001':
            for path in api_spec.get('paths', {}).keys():
                if not re.match('^/v[0-9]+/.*', path):
                    violations.append({
                        'id': rule['id'],
                        'description': f"{rule['description']} at path {path}",
                        'fix': rule.get('fix'),
                        'path': path
                    })

        # DOC001: Ensure all operations have a description
        elif rule['id'] == 'DOC001':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    if 'description' not in details or not details['description'].strip():
                        violations.append({
                            'id': rule['id'],
                            'description': f"{rule['description']} at {method.upper()} {path}",
                            'fix': rule.get('fix'),
                            'path': path,
                            'method': method
                        })

        # PARAM001: Ensure all path parameters are defined in components or inline
        elif rule['id'] == 'PARAM001':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    for param in details.get('parameters', []):
                        if param['in'] == 'path' and not param.get('schema'):
                            violations.append({
                                'id': rule['id'],
                                'description': f"{rule['description']} for parameter '{param['name']}' at {method.upper()} {path}",
                                'fix': rule.get('fix'),
                                'path': path,
                                'method': method
                            })

        # RESP001: Ensure all responses include a content type
        elif rule['id'] == 'RESP001':
            for path, methods in api_spec.get('paths', {}).items():
                for method, details in methods.items():
                    for response_code, response in details.get('responses', {}).items():
                        # Ensure that response is not None before checking for 'content'
                        if response is not None and 'content' not in response:
                            violations.append({
                                'id': rule['id'],
                                'description': f"{rule['description']} for response '{response_code}' at {method.upper()} {path}",
                                'fix': rule.get('fix'),
                                'path': path,
                                'method': method
                            })
        

    return violations

# Simple OpenAPI spec parser using PyYAML
def parse_openapi_spec(spec_file):
    with open(spec_file, 'r') as file:
        return yaml.safe_load(file)

def main():
    if len(sys.argv) < 3:
        print("Usage: cartlis_governance.py.py --spec api_spec.yaml [--fix]")
        sys.exit(1)

    api_spec_path = sys.argv[2]
    
    # Load and parse the OpenAPI spec using PyYAML
    api_spec = parse_openapi_spec(api_spec_path)

    # Load the base rules
    rules = load_rules('rules/base_rules.yaml')

    # Validate the spec
    violations = validate_spec(api_spec, rules)

    if violations:
        print(f"Found {len(violations)} violations:")
        for violation in violations:
            print(f"{violation['id']}: {violation['description']} at {violation.get('method', 'unknown').upper()} {violation['path']}")
        
        # Apply fixes if the --fix flag is present
        if '--fix' in sys.argv:
            api_spec = fix_spec(api_spec, violations)
            
            # Save the fixed spec to a new file
            fixed_spec_path = "fixed_api_spec.yaml"
            with open(fixed_spec_path, 'w') as file:
                yaml.dump(api_spec, file)
            
            print(f"All fixes have been applied and saved to {fixed_spec_path}.")
        else:
            print("Run the command again with --fix to apply fixes.")
    else:
        print("No violations found.")

if __name__ == "__main__":
    main()