#!/usr/bin/env python3
"""Offline administrative-boundary fixtures; never invokes the live GitHub API."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("protection", Path(__file__).with_name("branch-protection.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
SHA = "a" * 40
BASE = M.read_definition(M.DEFAULT_DEFINITION)
NEW_CHECK = {"context": "fixture additional check", "app_id": 15368}


def raw(document):
    policy = deepcopy(document["protection"])
    policy.pop("restrictions")
    for name in M.BOOL_FIELDS:
        policy[name] = {"enabled": policy[name]}
    status = policy["required_status_checks"]
    status["contexts"] = [check["context"] for check in status["checks"]]
    status["url"] = "https://api.github.com/status"
    status["contexts_url"] = "https://api.github.com/contexts"
    policy["required_pull_request_reviews"]["url"] = "https://api.github.com/reviews"
    policy["url"] = "https://api.github.com/protection"
    return policy


class Remote:
    """Stateful fake service: preserve all policy unless the test injects drift."""

    def __init__(self):
        self.state = deepcopy(BASE)
        self.events = []
        self.reads = 0
        self.drift_read = None
        self.rulesets = []
        self.rule = deepcopy(BASE["classic_rule"])
        self.run = {"name": NEW_CHECK["context"], "head_sha": SHA, "status": "completed",
                    "conclusion": "success", "app": {"id": 15368}}
        self.evidence = None

    def __call__(self, endpoint, payload=None):
        self.events.append((endpoint, deepcopy(payload)))
        if endpoint == "graphql":
            return {"data": {"repository": {"ref": {"branchProtectionRule": deepcopy(self.rule)}}}}
        if endpoint.endswith("/rulesets"):
            return deepcopy(self.rulesets)
        if "/check-runs?" in endpoint:
            return deepcopy(self.evidence if self.evidence is not None else {"total_count": 1, "check_runs": [self.run]})
        if payload is not None:
            if endpoint != M.ENDPOINT + "/required_status_checks":
                raise AssertionError("unexpected mutation endpoint")
            self.state["protection"]["required_status_checks"] = deepcopy(payload)
            return deepcopy(payload)
        if endpoint != M.ENDPOINT:
            raise AssertionError("unexpected read endpoint")
        self.reads += 1
        if self.reads == self.drift_read:
            self.state["protection"]["allow_force_pushes"] = True
        return raw(self.state)

    def writes(self):
        return [event for event in self.events if event[1] is not None and event[0] != "graphql"]


class ProtectionTests(unittest.TestCase):
    def setUp(self):
        self.remote = Remote()
        self.desired = deepcopy(BASE)
        self.desired["protection"]["required_status_checks"]["checks"].append(deepcopy(NEW_CHECK))
        self.desired = M.validate(self.desired)
        self.api_patch = patch.object(M, "api", self.remote)
        self.api_patch.start()
        self.addCleanup(self.api_patch.stop)
        self.env_patch = patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def rejected(self, desired=None, expected=None, sha=SHA):
        with self.assertRaises(M.PolicyError):
            M.apply(self.desired if desired is None else desired, BASE if expected is None else expected, sha)
        self.assertEqual(self.remote.writes(), [])

    def test_addition_uses_only_narrow_patch_and_full_readback(self):
        self.assertIn("read-back matches", M.apply(self.desired, BASE, SHA))
        self.assertEqual(self.remote.writes(), [(M.ENDPOINT + "/required_status_checks", self.desired["protection"]["required_status_checks"])])
        self.assertEqual(self.remote.state, self.desired)
        self.assertEqual(self.remote.reads, 3)

    def test_matching_policy_is_a_real_noop(self):
        self.assertIn("no write needed", M.apply(BASE, BASE, SHA))
        self.assertEqual(self.remote.writes(), [])
        self.assertEqual(self.remote.reads, 2)

    def test_baseline_drift_stops_before_evidence_or_write(self):
        self.remote.state["protection"]["required_linear_history"] = False
        self.rejected()
        self.assertFalse(any("check-runs" in event[0] for event in self.remote.events))

    def test_drift_immediately_before_write_stops(self):
        self.remote.drift_read = 2
        self.rejected()

    def test_postwrite_drift_fails_without_automatic_rollback(self):
        self.remote.drift_read = 3
        with self.assertRaisesRegex(M.PolicyError, "read-back differs"):
            M.apply(self.desired, BASE, SHA)
        self.assertEqual(len(self.remote.writes()), 1)

    def test_new_or_inherited_rulesets_stop(self):
        self.remote.rulesets = [{"id": 1}]
        self.rejected()
        self.assertEqual(self.remote.reads, 0)

    def test_every_ci_marker_refuses_even_before_read(self):
        for marker in ("CI", "GITHUB_ACTIONS", "GITHUB_RUN_ID", "RUNNER_ENVIRONMENT"):
            with self.subTest(marker=marker), patch.dict(os.environ, {marker: "false"}):
                self.rejected()
        self.assertEqual(self.remote.events, [])

    def test_check_removal_is_refused(self):
        self.desired["protection"]["required_status_checks"]["checks"].pop(0)
        self.rejected()

    def test_binding_change_is_refused(self):
        self.desired["protection"]["required_status_checks"]["checks"][0]["app_id"] = 999
        self.rejected()

    def test_strict_change_is_refused(self):
        self.desired["protection"]["required_status_checks"]["strict"] = False
        self.rejected()

    def test_every_nonstatus_policy_change_is_refused(self):
        for field in M.BOOL_FIELDS:
            changed = deepcopy(self.desired)
            changed["protection"][field] = not changed["protection"][field]
            with self.subTest(field=field):
                self.rejected(desired=changed)
        changed = deepcopy(self.desired)
        changed["protection"]["required_pull_request_reviews"]["required_approving_review_count"] = 1
        self.rejected(desired=changed)

    def test_unverified_statuses_are_refused(self):
        for conclusion in ("failure", "cancelled", "neutral", "skipped", None):
            self.remote.run["conclusion"] = conclusion
            with self.subTest(conclusion=conclusion):
                self.rejected()

    def test_incomplete_run_is_refused(self):
        self.remote.run["status"] = "in_progress"
        self.rejected()

    def test_wrong_sha_is_refused(self):
        self.remote.run["head_sha"] = "b" * 40
        self.rejected()

    def test_wrong_or_untyped_source_app_is_refused(self):
        for app in (999, None, True, "15368"):
            self.remote.run["app"]["id"] = app
            with self.subTest(app=app):
                self.rejected()

    def test_full_sha_is_mandatory_even_for_noop(self):
        for sha in ("a" * 7, "A" * 40, "a" * 39, "", None):
            with self.subTest(sha=sha):
                self.rejected(desired=BASE, sha=sha)

    def test_missing_duplicate_or_truncated_check_evidence_is_refused(self):
        for evidence in ({"total_count": 0, "check_runs": []},
                         {"total_count": 2, "check_runs": [self.remote.run, self.remote.run]},
                         {"total_count": 101, "check_runs": [self.remote.run]},
                         {"total_count": 2, "check_runs": [self.remote.run]},
                         {"total_count": True, "check_runs": [self.remote.run]}):
            self.remote.evidence = evidence
            with self.subTest(evidence=evidence):
                self.rejected()

    def test_unknown_live_policy_is_not_silently_dropped(self):
        for location in ((), ("enforce_admins",), ("required_pull_request_reviews",), ("required_status_checks",)):
            response = raw(BASE)
            target = response
            for part in location:
                target = target[part]
            target["unexpected_policy"] = True
            with self.subTest(location=location), self.assertRaises(M.PolicyError):
                M.normalize(response, BASE["classic_rule"])

    def test_graphql_deployment_and_actor_policy_extensions_stop_apply(self):
        for field, value in (("requiresDeployments", True), ("requiredDeploymentEnvironments", ["production"]),
                             ("bypassPullRequestAllowances", {"totalCount": 1}),
                             ("requiresApprovingReviews", False), ("restrictsReviewDismissals", True)):
            self.remote.rule = deepcopy(BASE["classic_rule"])
            self.remote.rule[field] = value
            with self.subTest(field=field):
                self.rejected()

    def test_push_restrictions_are_explicitly_unrepresentable(self):
        response = raw(BASE)
        response["restrictions"] = {"users": [], "teams": [], "apps": []}
        with self.assertRaises(M.PolicyError):
            M.normalize(response, BASE["classic_rule"])

    def test_contexts_must_match_bound_checks(self):
        response = raw(BASE)
        response["required_status_checks"]["contexts"].pop()
        with self.assertRaises(M.PolicyError):
            M.normalize(response, BASE["classic_rule"])

    def test_missing_policy_is_not_defaulted(self):
        response = raw(BASE)
        response.pop("lock_branch")
        with self.assertRaises(M.PolicyError):
            M.normalize(response, BASE["classic_rule"])

    def test_definition_types_unknown_fields_duplicates_are_refused(self):
        for mutate in (lambda d: d.update(extra=True), lambda d: d.update(schema_version=True),
                       lambda d: d.update(repository="another/repo"),
                       lambda d: d["protection"].update(enforce_admins="false"),
                       lambda d: d["protection"]["required_status_checks"]["checks"][0].update(app_id=-1),
                       lambda d: d["protection"]["required_status_checks"]["checks"][0].update(app_id=True),
                       lambda d: d["protection"]["required_status_checks"]["checks"].append(d["protection"]["required_status_checks"]["checks"][0])):
            changed = deepcopy(BASE)
            mutate(changed)
            with self.assertRaises(M.PolicyError):
                M.validate(changed)
        with self.assertRaises(M.PolicyError):
            M.decode('{"strict":true,"strict":false}')

    def cli(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = M.main(args)
            except SystemExit as error:
                rc = error.code
        return rc, out.getvalue(), err.getvalue()

    def test_readonly_export_check_and_drift_diff(self):
        rc, out, _ = self.cli(["export"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out), BASE)
        self.assertEqual(self.cli(["check"])[0], 0)
        self.remote.state["protection"]["lock_branch"] = True
        rc, out, _ = self.cli(["check"])
        self.assertEqual(rc, 1)
        self.assertIn('"lock_branch": true', out)
        self.assertEqual(self.remote.writes(), [])

    def test_cli_errors_and_bad_json_never_call_remote(self):
        for args in ([], ["unknown"], ["apply"], ["check", "--def", "x"], ["export", "extra"]):
            self.assertEqual(self.cli(args)[0], 2)
        self.assertEqual(self.cli(["--help"])[0], 0)
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid.json"
            invalid.write_text('{"broken":')
            self.assertEqual(self.cli(["check", "--definition", str(invalid)])[0], 1)
        self.assertEqual(self.remote.events, [])

    def test_actual_api_transport_is_fixed_host_explicit_method_and_stdin_json(self):
        payload = self.desired["protection"]["required_status_checks"]
        with patch.object(M.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "{}", "")) as runner:
            # Invoke the real transport, bypassing only this test's fake api.
            self.api_patch.stop()
            M.api(M.ENDPOINT + "/required_status_checks", payload)
            command = runner.call_args.args[0]
            self.assertIn("github.com", command)
            self.assertIn("PATCH", command)
            self.assertEqual(command[-2:], ["--input", "-"])
            self.assertEqual(json.loads(runner.call_args.kwargs["input"]), payload)
            self.assertEqual(runner.call_args.kwargs["timeout"], 30)

    def test_transport_failure_never_echoes_credentials(self):
        self.api_patch.stop()
        with patch.object(M.subprocess, "run", return_value=subprocess.CompletedProcess([], 22, "", "fixture-secret-token")):
            rc, out, err = self.cli(["export"])
        self.assertEqual(rc, 1)
        self.assertNotIn("fixture-secret-token", out + err)


if __name__ == "__main__":
    unittest.main()
