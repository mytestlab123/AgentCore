#!/usr/bin/env python3
"""Offline regression tests for Issue #46's EC2 read-only IAM grant."""

from __future__ import annotations

import os
import unittest
from unittest import mock

import gateway_policy_poc as poc
import issue46_authorize_ec2_security_group_read as issue46


class Issue46AuthorizeEc2SecurityGroupReadTests(unittest.TestCase):
    def test_document_is_one_required_read_only_list_action(self):
        document = issue46.policy_document()
        statement = document["Statement"][0]
        self.assertEqual(statement["Action"], "ec2:DescribeSecurityGroups")
        self.assertEqual(statement["Resource"], "*")
        self.assertEqual(statement["Effect"], "Allow")

    def test_plan_needs_no_aws_or_role(self):
        with mock.patch.object(issue46, "authorize") as authorize, \
                mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(issue46.main([]), 0)
        authorize.assert_not_called()

    def test_role_name_refuses_path_or_option(self):
        for value in ("", "role/with/path", "-unexpected"):
            with mock.patch.dict(os.environ, {issue46.ROLE_ENV: value}, clear=False):
                with self.assertRaises(poc.Blocked):
                    issue46.require_role_name()


if __name__ == "__main__":
    unittest.main()
