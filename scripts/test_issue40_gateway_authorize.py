#!/usr/bin/env python3
"""Offline regression tests for the narrow Issue #40 Cedar authorization."""

import os
import unittest
from unittest import mock

import gateway_policy_poc as poc
import issue40_gateway_authorize as issue40


PRINCIPAL = "arn:aws:sts::111122223333:assumed-role/LibreChatEc2Role"
GATEWAY = "arn:aws:bedrock-agentcore:ap-southeast-1:111122223333:gateway/demo"


class Issue40GatewayAuthorizeTests(unittest.TestCase):
    def test_policy_is_exact_role_tool_gateway_and_dev_only(self):
        statement = issue40.librechat_statement(PRINCIPAL, GATEWAY)
        self.assertIn(PRINCIPAL, statement)
        self.assertIn(poc.FULL_TOOL_NAME, statement)
        self.assertIn(GATEWAY, statement)
        self.assertIn('context.input.environment == "dev"', statement)
        with self.assertRaises(poc.Blocked):
            issue40.librechat_statement("arn:aws:iam::111122223333:role/too-broad", GATEWAY)

    def test_plan_needs_no_aws_or_principal(self):
        with mock.patch.object(issue40, "authorize") as authorize, \
                mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(issue40.main([]), 0)
        authorize.assert_not_called()

    def test_policy_inventory_allows_only_retained_and_new_policy(self):
        retained = {"name": poc.POLICY_NAME}
        new = {"name": issue40.POLICY_NAME}
        issue40.assert_policy_names([retained], allow_new=False)
        issue40.assert_policy_names([retained, new], allow_new=True)
        with self.assertRaises(poc.Blocked):
            issue40.assert_policy_names([retained, {"name": "unexpected"}], allow_new=True)


if __name__ == "__main__":
    unittest.main()
