#!/usr/bin/env python3
"""Offline regression tests for Issue #40's exact EC2 Gateway IAM grant."""

from __future__ import annotations

import os
import unittest
from unittest import mock

import gateway_policy_poc as poc
import issue40_authorize_ec2_gateway as issue40


GATEWAY = "arn:aws:bedrock-agentcore:ap-southeast-1:111122223333:gateway/demo"


class Issue40AuthorizeEc2GatewayTests(unittest.TestCase):
    def test_document_is_one_action_on_one_retained_gateway(self):
        document = issue40.policy_document(GATEWAY)
        statement = document["Statement"][0]
        self.assertEqual(statement["Action"], "bedrock-agentcore:InvokeGateway")
        self.assertEqual(statement["Resource"], GATEWAY)
        self.assertEqual(statement["Effect"], "Allow")

    def test_plan_needs_no_aws_or_role(self):
        with mock.patch.object(issue40, "authorize") as authorize, \
                mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(issue40.main([]), 0)
        authorize.assert_not_called()

    def test_role_name_refuses_path_or_option(self):
        for value in ("", "role/with/path", "-unexpected"):
            with mock.patch.dict(os.environ, {issue40.ROLE_ENV: value}, clear=False):
                with self.assertRaises(poc.Blocked):
                    issue40.require_role_name()


if __name__ == "__main__":
    unittest.main()
