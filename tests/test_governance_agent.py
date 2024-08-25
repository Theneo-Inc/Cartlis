import unittest
from cartlis_governance.py import validate_spec, load_rules

class TestGovernanceAgent(unittest.TestCase):
    def test_security_rule(self):
        # Example API spec without security
        api_spec = {
            "openapi": "3.0.0",
            "paths": {
                "/transactions": {
                    "post": {
                        "summary": "Create a new transaction"
                    }
                }
            }
        }
        rules = load_rules('rules/base_rules.yaml')
        violations = validate_spec(api_spec, rules)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['id'], 'SEC002')

if __name__ == '__main__':
    unittest.main()
