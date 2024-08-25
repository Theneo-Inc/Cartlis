"""
Usage:
python client.py --api-spec-file ../openapi-specs/hivelocity.yaml
"""

import os
from datetime import datetime

import yaml
from openai import OpenAI

from constants import RULE_GENERATION_SYSTEM_MESSAGE, RULE_VALIDATION_SYSTEM_MESSAGE

# Constants
BASE_RULES_FILE_PATH = "base_rules.yaml"


# Environment Variables
API_SPEC_FILE_PATH = os.environ.get("API_SPEC_FILE_PATH")
COMPLIANCE_STANDARDS = os.environ.get("COMPLIANCE_STANDARDS")
MODEL_URL = os.environ.get("MODEL_URL")
MODEL_NAME = os.environ.get("MODEL_NAME")
MODEL_KEY = os.environ.get("MODEL_KEY", "EMPTY")
TEMP = float(os.environ.get("TEMP", 0.3))

if not MODEL_URL.endswith("/v1"):
    MODEL_URL = f"{MODEL_URL}/v1"

client = OpenAI(
    api_key=MODEL_KEY,
    base_url=MODEL_URL,
)
# stop_token_ids = "128009,128001"


def read_api_spec_file(api_spec_file_path):
    with open(api_spec_file_path, "r") as f:
        return f.read()


def generate_rules(api_spec_file_path, compliance_standards):
    """
    Generate rules for the API spec file. Inference 30-60 seconds.
    """
    api_spec_file_str = read_api_spec_file(api_spec_file_path)
    print(f"Loaded API spec from {api_spec_file_path}")

    user_message = f"""
    I require the {compliance_standards} compliance standards. Here's my API spec:
    {api_spec_file_str}
    """

    print(f"Assembled user message, compliances: {compliance_standards}")

    messages = [
        {"role": "system", "content": RULE_GENERATION_SYSTEM_MESSAGE},
        {"role": "user", "content": user_message},
    ]

    t_one = datetime.now()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMP,
        stream=False,
    )
    t_two = datetime.now()
    duration = t_two - t_one

    response_content = completion.choices[0].message.content
    usage = completion.usage

    yaml_content = (
        response_content.split("```yaml")[1].split("```")[0]
        if "```yaml" in response_content
        else response_content.split("```yml")[1].split("```")[0]
    )
    yaml_content = yaml_content.strip()
    # print(yaml_content)
    # print(
    #     f"Tokens - prompt {usage.prompt_tokens}, completion {usage.completion_tokens}, total {usage.total_tokens}"
    # )
    # print(f"Duration: {duration.seconds} seconds")

    return (
        yaml_content,
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
        duration.seconds,
    )


def update_base_rules(base_rules_path: str, new_rules: str):
    with open(base_rules_path, "r") as f:
        base_rules = yaml.safe_load(f)

    new_rules_dict = yaml.safe_load(new_rules)

    # Ensure both base_rules and new_rules_dict have a 'rules' key at the top level
    if "rules" not in base_rules:
        base_rules = {"rules": base_rules}
    if "rules" not in new_rules_dict:
        new_rules_dict = {"rules": new_rules_dict}

    print(f"# base rules: {len(base_rules['rules'])}")
    print(f"# new rules: {len(new_rules_dict['rules'])}")
    # Merge the rules lists
    merged_rules = {"rules": base_rules["rules"] + new_rules_dict["rules"]}

    print(f"# merged rules: {len(merged_rules['rules'])}")

    return merged_rules


def write_rules_to_file(rules, output_path: str):
    with open(output_path, "w") as f:
        yaml.dump(rules, f)


def generate_validation_functions(rules: dict):
    """
    Generate validation functions for the rules. Inference ~30 seconds.
    """
    print(f"Generating validation functions for {len(rules['rules'])} rules")
    rules_str = yaml.dump(rules)
    user_message = f"""
    Here's my ruleset:
    {rules_str}
    """

    messages = [
        {"role": "system", "content": RULE_VALIDATION_SYSTEM_MESSAGE},
        {"role": "user", "content": user_message},
    ]

    t_one = datetime.now()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMP,
        stream=False,
    )
    t_two = datetime.now()
    duration = t_two - t_one

    response_content = completion.choices[0].message.content

    python_code = response_content.split("```python")[1].split("```")[0]
    print(f"Generated validation functions in {duration.seconds} seconds")
    return python_code, duration.seconds


def write_validation_functions_to_file(validation_functions, output_path: str):
    with open(output_path, "w") as f:
        f.write(validation_functions)


def get_validation_functions():
    import validation_functions
    import inspect

    functions = {
        name: func
        for name, func in inspect.getmembers(validation_functions, inspect.isfunction)
    }

    return functions


# new_rules, _, _, _, _ = generate_rules(API_SPEC_FILE_PATH, COMPLIANCE_STANDARDS)
# merged_rules = update_base_rules(BASE_RULES_FILE_PATH, new_rules)
# write_rules_to_file(merged_rules, "new_rules.yaml")

# with open("new_rules.yaml", "r") as f:
#     merged_rules = yaml.safe_load(f)

# validation_functions, duration_seconds = generate_validation_functions(merged_rules)

# write_validation_functions_to_file(validation_functions, "validation_functions.py")
# validation_functions = get_validation_functions()
# print(validation_functions)
# for name, func in validation_functions.items():
#     print(f"{name}: {func.__doc__}")
