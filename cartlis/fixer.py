import yaml
import re
import os
import openai
import requests
from openapi_spec_validator import validate_spec
from openapi_spec_validator.exceptions import OpenAPISpecValidatorError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# AI content generation function
def generate_ai_content(prompt):
    try:
        response = openai.ChatCompletion.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are an assistant that generates API content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
        )
        return response.choices[0]['message']['content'].strip()
    except Exception as e:
        print(f"AI generation failed: {e}")
        return "This is a fallback placeholder."

# Apply fixes to the API spec based on violations
def apply_fix(api_spec, violation):
    path = violation.get('path')
    method = violation.get('method')
    fix_snippet = violation.get('fix', {}).get('fix_snippet', {})
    
    if path and method and fix_snippet:
        print(f"Applying fix to {method.upper()} operation in {path}")
        if 'security' not in api_spec['paths'][path][method]:
            api_spec['paths'][path][method]['security'] = fix_snippet['security']
        else:
            print(f"Security already exists for {method.upper()} in {path}")
    return api_spec

# Fix the spec based on the violations
def fix_spec(api_spec, violations):
    for violation in violations:
        # Ensure the 'method' and 'path' keys are present
        path = violation.get('path')
        method = violation.get('method')

        if not method:
            print(f"Skipping violation because 'method' is missing: {violation}")
            continue

        if not path:
            print(f"Skipping violation because 'path' is missing: {violation}")
            continue

        print(f"Applying fix for violation: {violation['id']} at {method.upper()} {path}")

        # SEC002: Add OAuth2 scopes to the security definition
        if violation['id'] == 'SEC002':
            if path in api_spec['paths'] and method in api_spec['paths'][path]:
                api_spec['paths'][path][method]['security'] = [
                    {
                        "OAuth2": ["write", "read"]  # Array of strings instead of an object
                    }
                ]
                print(f"Added OAuth2 scopes to {method.upper()} {path}")

        # SEC003: Update server URLs to HTTPS
        elif violation['id'] == 'SEC003':
            for server in api_spec.get('servers', []):
                if "http://" in server['url']:
                    server['url'] = server['url'].replace("http://", "https://")
                    print(f"Updated server URL to HTTPS: {server['url']}")

        # SEC004: Add a default security scheme if missing
        elif violation['id'] == 'SEC004':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                if 'security' not in api_spec['paths'][violation['path']][violation['method']]:
                    api_spec['paths'][violation['path']][violation['method']]['security'] = [
                        {
                            "OAuth2": {
                                "flows": {
                                    "implicit": {
                                        "authorizationUrl": "https://example.com/oauth/authorize",
                                        "scopes": {
                                            "read": "Grants read access",
                                            "write": "Grants write access"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                    print(f"Added default security scheme to {violation['method'].upper()} {violation['path']}")

        # PERF001: Add rate limiting headers
        elif violation['id'] == 'PERF001':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                responses = api_spec['paths'][violation['path']][violation['method']].get('responses', {})
                if "200" in responses:
                    if 'headers' not in responses["200"]:
                        responses["200"]['headers'] = {}
                    responses["200"]['headers'].update({
                        "X-RateLimit-Limit": {"schema": {"type": "integer"}},
                        "X-RateLimit-Remaining": {"schema": {"type": "integer"}},
                        "X-RateLimit-Reset": {"schema": {"type": "integer"}}
                    })
                    print(f"Added rate limiting headers to {violation['method'].upper()} {violation['path']} response 200")

        # PERF002: Add Cache-Control headers
        elif violation['id'] == 'PERF002':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                responses = api_spec['paths'][violation['path']][violation['method']].get('responses', {})
                if "200" in responses:
                    if 'headers' not in responses["200"]:
                        responses["200"]['headers'] = {}
                    responses["200"]['headers']['Cache-Control'] = {
                        "schema": {"type": "string", "description": "Caching directive for improving performance"}
                    }
                    print(f"Added Cache-Control headers to {violation['method'].upper()} {violation['path']} response 200")

        # CONSIST001: Convert parameter names to snake_case
        elif violation['id'] == 'CONSIST001':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                for param in api_spec['paths'][violation['path']][violation['method']].get('parameters', []):
                    if 'name' in param:
                        original_name = param['name']
                        param['name'] = to_snake_case(param['name'])
                        print(f"Renamed parameter '{original_name}' to '{param['name']}' in {violation['method'].upper()} {violation['path']}")

        # CONSIST002: Convert schema properties to camelCase
        elif violation['id'] == 'CONSIST002':
            if violation['schema'] in api_spec['components']['schemas']:
                schema = api_spec['components']['schemas'][violation['schema']]
                new_properties = {}
                for property_name, property_value in schema.get('properties', {}).items():
                    new_name = to_camel_case(property_name)
                    new_properties[new_name] = property_value
                    print(f"Renamed property '{property_name}' to '{new_name}' in schema {violation['schema']}")
                schema['properties'] = new_properties

        # DEP001: Mark deprecated endpoints and add a deprecation notice
        elif violation['id'] == 'DEP001':
            if violation['path'] in api_spec['paths']:
                for method in api_spec['paths'][violation['path']]:
                    api_spec['paths'][violation['path']][method]['deprecated'] = True
                    if 'description' in api_spec['paths'][violation['path']][method]:
                        api_spec['paths'][violation['path']][method]['description'] += "\nUse the following alternative: /v2/transactions."
                    print(f"Marked {method.upper()} {violation['path']} as deprecated and added alternative.")

        # VER001: Add versioning to paths
        elif violation['id'] == 'VER001':
            if violation['path'] in api_spec['paths']:
                new_path = "/v1" + violation['path']
                api_spec['paths'][new_path] = api_spec['paths'].pop(violation['path'])
                print(f"Added versioning to path {violation['path']} -> {new_path}")
        

        # DOC001: Use AI to generate descriptions if missing
        if violation['id'] == 'DOC001':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                method_spec = api_spec['paths'][violation['path']][violation['method']]
                if not method_spec.get('description'):
                    method_spec['description'] = generate_ai_content(f"Generate a description for {violation['method'].upper()} {violation['path']}")
                    print(f"Generated description for {violation['method'].upper()} {violation['path']}")

        # OP_ID001: AI-Generated Operation ID
        elif violation['id'] == 'OP_ID001':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                prompt = f"Generate a unique operation ID for an API operation handling {violation['method'].upper()} request at {violation['path']}."
                ai_operation_id = generate_ai_content(prompt)
                if ai_operation_id:
                    api_spec['paths'][violation['path']][violation['method']]['operationId'] = ai_operation_id
                    print(f"Added AI-generated operationId to {violation['method'].upper()} {violation['path']}")
                else:
                    api_spec['paths'][violation['path']][violation['method']]['operationId'] = f"operationId_placeholder_{violation['method']}"
                    print(f"Added fallback placeholder operationId to {violation['method'].upper()} {violation['path']}")

        # PARAM001: Add missing path parameter definitions
        if violation['id'] == 'PARAM001' or violation['id'] == 'UnresolvableParameterError':  # Catch other cases as well
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                # Check if the path parameter is defined
                path_parameters = api_spec['paths'][violation['path']][violation['method']].get('parameters', [])
                param_names = [param['name'] for param in path_parameters if param['in'] == 'path']
                
                # Find missing path parameters from the path itself (e.g., {id})
                missing_params = re.findall(r'{(.*?)}', violation['path'])
                
                for param in missing_params:
                    if param not in param_names:
                        # Add the missing path parameter definition
                        path_parameters.append({
                            "name": param,
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            },
                            "description": f"The {param} path parameter"
                        })
                        api_spec['paths'][violation['path']][violation['method']]['parameters'] = path_parameters
                        print(f"Added missing path parameter '{param}' to {violation['method'].upper()} {violation['path']}")

        # PARAM_DESC001: Add AI-generated descriptions for parameters lacking descriptions
        elif violation['id'] == 'PARAM_DESC001':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                for param in api_spec['paths'][violation['path']][violation['method']].get('parameters', []):
                    if not param.get('description'):
                        param['description'] = generate_ai_content(f"Generate a description for the {param['name']} parameter in the {violation['method'].upper()} operation at {violation['path']}.")
                        print(f"Generated description for parameter '{param['name']}' in {violation['method'].upper()} {violation['path']}")

        # RESP001: Add default content type to responses
        if violation['id'] == 'RESP001':
            if violation['path'] in api_spec['paths'] and violation['method'] in api_spec['paths'][violation['path']]:
                responses = api_spec['paths'][violation['path']][violation['method']].get('responses', {})

                # Ensure responses is a dictionary and iterate over it
                if responses:
                    for status_code, response in responses.items():
                        # Ensure response is not None
                        if response is None:
                            response = {}
                            responses[status_code] = response
                        
                        # Ensure 'content' is present in the response
                        if 'content' not in response:
                            response['content'] = {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Pet"  # Adjust this reference as per your schema
                                    }
                                }
                            }
                            print(f"Added content type to response {status_code} in {violation['method'].upper()} {violation['path']}")

                        # Ensure headers are correctly added and formatted
                        if 'headers' not in response:
                            response['headers'] = {}
                        headers = response['headers']

                        # Add common headers, ensuring they have the correct structure
                        headers['X-RateLimit-Limit'] = {"schema": {"type": "integer"}}
                        headers['X-RateLimit-Remaining'] = {"schema": {"type": "integer"}}
                        headers['X-RateLimit-Reset'] = {"schema": {"type": "integer"}}
                        headers['Cache-Control'] = {"schema": {"type": "string", "description": "Caching directive for improving performance"}}

                        print(f"Added headers to response {status_code} in {violation['method'].upper()} {violation['path']}")
        
       # Ensure the requestBody description is not None
        if 'requestBody' in api_spec['paths'][path][method]:
            request_body = api_spec['paths'][path][method]['requestBody']
            if request_body.get('description') is None:
                request_body['description'] = "Description not provided."
                print(f"Added default description to requestBody in {method.upper()} {path}")

        # OP_SUM001: Add AI-generated summaries for operations lacking summaries
        elif violation['id'] == 'OP_SUM001':
            if path in api_spec['paths'] and method in api_spec['paths'][path]:
                method_spec = api_spec['paths'][path][method]
                if not method_spec.get('summary'):
                    method_spec['summary'] = generate_ai_content(f"Generate a concise summary for the {method.upper()} operation at {path}.")
                    print(f"Generated AI summary for {method.upper()} {path}")


        # SCHEMA_DESC001: Add AI-generated descriptions to schema object fields
        elif violation['id'] == 'SCHEMA_DESC001':
            if violation['schema'] in api_spec['components']['schemas']:
                schema = api_spec['components']['schemas'][violation['schema']]
                for property_name, property_value in schema.get('properties', {}).items():
                    if 'description' not in property_value:
                        property_value['description'] = generate_ai_content(f"Generate a description for the '{property_name}' field in the {violation['schema']} schema.")
                        print(f"Generated AI description for schema field '{property_name}' in {violation['schema']}")
        
        # Fix None responses before any other processing
        for path, methods in api_spec.get('paths', {}).items():
            for method, details in methods.items():
                responses = details.get('responses', {})
                for response_code, response in responses.items():
                    if response is None:
                        # Replace None response with a default response object
                        print(f"Fixing None response for status code {response_code} in {method.upper()} {path}")
                        responses[response_code] = {
                            "description": "Default response"
                        }
        # Apply the versioning fix
        if violation['id'] == 'VER001':
            if violation['path'] in api_spec['paths']:
                new_path = "/v1" + violation['path']
                api_spec['paths'][new_path] = api_spec['paths'].pop(violation['path'])
                print(f"Added versioning to path {violation['path']} -> {new_path}")
                
                # Update the path in violations so subsequent fixes use the new path
                for v in violations:
                    if v['path'] == violation['path']:
                        v['path'] = new_path
        # Ensure the correct path is referenced after versioning fix
        for violation in violations:
            path = violation.get('path')
            method = violation.get('method')

            # Check if path and method are available in the violation before proceeding
            if not path:
                print(f"Skipping violation due to missing path: {violation}")
                continue

            if not method:
                print(f"Skipping violation due to missing method: {violation}")
                continue

            if path in api_spec['paths'] and method in api_spec['paths'][path]:
                # Apply fixes as usual
                # Example: Apply RESP001 fix
                if violation['id'] == 'RESP001':
                    responses = api_spec['paths'][path][method].get('responses', {})
                    # Ensure response handling logic continues here
                    for status_code, response in responses.items():
                        if response is None:
                            # Replace None response with a default response object
                            print(f"Fixing None response for status code {status_code} in {method.upper()} {path}")
                            responses[status_code] = {
                                "description": "Default response"
                            }
            else:
                print(f"Path {path} or method {method} no longer exists after versioning fix")


    # Validate the fixed spec
        try:
            validate_spec(api_spec)
        except OpenAPISpecValidatorError as e:
            print(f"Validation error: {e}")

        # Save the fixed spec
        with open("fixed_api_spec.yaml", "w") as file:
            yaml.dump(api_spec, file, sort_keys=False)

        print("All fixes have been applied and saved to fixed_api_spec.yaml")
        return api_spec

# Helper functions for naming conventions
def to_snake_case(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def to_camel_case(name):
    parts = name.split('_')
    return parts[0] + ''.join(x.title() for x in parts[1:])