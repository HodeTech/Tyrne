#!/usr/bin/env python3
"""Export/check classic main protection; explicitly apply additive checks locally.

Bound to HodeTech/Tyrne on github.com. Unknown or unrepresentable policy fails
closed. Apply never rewrites the full protection: only required status checks
can change, after an explicit expected-current snapshot and remote-green proof.
"""

import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPOSITORY = "HodeTech/Tyrne"
BRANCH = "main"
ENDPOINT = f"repos/{REPOSITORY}/branches/{BRANCH}/protection"
DEFAULT_DEFINITION = Path(__file__).resolve().parents[1] / ".github/branch-protection/main.json"
BOOL_FIELDS = (
    "required_signatures", "enforce_admins", "required_linear_history",
    "allow_force_pushes", "allow_deletions", "block_creations",
    "required_conversation_resolution", "lock_branch", "allow_fork_syncing",
)
REVIEW_BOOLS = ("dismiss_stale_reviews", "require_code_owner_reviews", "require_last_push_approval")
REVIEW_FIELDS = {*REVIEW_BOOLS, "required_approving_review_count"}
POLICY_FIELDS = {*BOOL_FIELDS, "required_status_checks", "required_pull_request_reviews", "restrictions"}
SUPPORTED_RULE = {
    "pattern": "main", "requiresApprovingReviews": True,
    "requiresDeployments": False, "requiredDeploymentEnvironments": [],
    "restrictsPushes": False, "restrictsReviewDismissals": False,
    "bypassForcePushAllowances": {"totalCount": 0},
    "bypassPullRequestAllowances": {"totalCount": 0},
    "reviewDismissalAllowances": {"totalCount": 0}, "pushAllowances": {"totalCount": 0},
}
RULE_QUERY = '''query {repository(owner:"HodeTech",name:"Tyrne") {
ref(qualifiedName:"refs/heads/main") {branchProtectionRule {
pattern requiresApprovingReviews requiresDeployments requiredDeploymentEnvironments
restrictsPushes restrictsReviewDismissals
bypassForcePushAllowances(first:1) {totalCount}
bypassPullRequestAllowances(first:1) {totalCount}
reviewDismissalAllowances(first:1) {totalCount} pushAllowances(first:1) {totalCount}
}}}}'''


class PolicyError(Exception):
    """An input, drift or remote verification prevents safe reconciliation."""


def require(condition, message):
    if not condition:
        raise PolicyError(message)


def fields(value, expected, label, optional=()):
    require(type(value) is dict, f"{label}: expected an object")
    require(set(value) <= set(expected) | set(optional), f"{label}: unknown/unrepresentable fields")
    require(set(expected) <= set(value), f"{label}: missing policy fields")


def boolean(value, label):
    require(type(value) is bool, f"{label}: expected a boolean")
    return value


def checks(value):
    require(type(value) is list and value, "checks: expected a nonempty array")
    names = set()
    for check in value:
        fields(check, {"context", "app_id"}, "check")
        name, app = check["context"], check["app_id"]
        require(type(name) is str and name.strip() == name and name, "check: invalid context")
        require(name not in names, "check: duplicate context")
        require(type(app) is int and app > 0, "check: explicit positive source app_id required")
        names.add(name)
    return sorted(value, key=lambda check: check["context"])


def validate(document):
    fields(document, {"schema_version", "repository", "branch", "protection", "classic_rule", "rulesets"}, "definition")
    require(type(document["schema_version"]) is int and document["schema_version"] == 1, "unsupported schema version")
    require(document["repository"] == REPOSITORY and document["branch"] == BRANCH, "definition must target HodeTech/Tyrne main")
    # GraphQL exposes deployment/actor allowances not present in the REST
    # protection response. Preserve the captured baseline; extensions fail closed.
    require(rendered(document["classic_rule"]) == rendered(SUPPORTED_RULE), "classic rule has unrepresentable deployment/review/actor policy")
    require(document["rulesets"] == [], "definition must preserve the no-rulesets baseline")
    policy = document["protection"]
    fields(policy, POLICY_FIELDS, "protection")
    for field in BOOL_FIELDS:
        boolean(policy[field], field)
    require(policy["restrictions"] is None, "push restrictions are not representable by this tool; reconcile before proceeding")
    review = policy["required_pull_request_reviews"]
    fields(review, REVIEW_FIELDS, "reviews")
    for field in REVIEW_BOOLS:
        boolean(review[field], field)
    count = review["required_approving_review_count"]
    require(type(count) is int and 0 <= count <= 6, "reviews: invalid approving count")
    status = policy["required_status_checks"]
    fields(status, {"strict", "checks"}, "status checks")
    boolean(status["strict"], "strict")
    status["checks"] = checks(status["checks"])
    return document


def without_urls(value, expected, label, optional=()):
    fields(value, expected, label, {*optional, "url"})
    if "url" in value:
        require(type(value["url"]) is str, f"{label}: invalid response URL")
    return {key: item for key, item in value.items() if key != "url"}


def normalize(response, rule):
    """Remove only known response metadata, never an unknown policy property."""
    policy = without_urls(response, POLICY_FIELDS - {"restrictions"}, "live protection", {"restrictions"})
    for field in BOOL_FIELDS:
        wrapped = without_urls(policy[field], {"enabled"}, field)
        policy[field] = boolean(wrapped["enabled"], field)
    policy.setdefault("restrictions", None)
    policy["required_pull_request_reviews"] = without_urls(policy["required_pull_request_reviews"], REVIEW_FIELDS, "live reviews")
    status = without_urls(policy["required_status_checks"], {"strict", "checks", "contexts"}, "live status checks", {"contexts_url"})
    if "contexts_url" in status:
        require(type(status.pop("contexts_url")) is str, "invalid contexts URL")
    contexts = status.pop("contexts")
    require(type(contexts) is list and all(type(item) is str for item in contexts), "invalid live contexts")
    bindings = checks(status["checks"])
    require(sorted(contexts) == sorted(check["context"] for check in bindings), "live contexts/check bindings disagree")
    policy["required_status_checks"] = status
    return validate({"schema_version": 1, "repository": REPOSITORY, "branch": BRANCH,
                     "protection": policy, "classic_rule": rule, "rulesets": []})


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(text):
    return json.loads(text, object_pairs_hook=unique_object)


def read_definition(path):
    return validate(decode(Path(path).read_text()))


def rendered(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def api(endpoint, payload=None):
    command = ["gh", "api", "--hostname", "github.com", "-H", "X-GitHub-Api-Version: 2022-11-28", endpoint,
               "--method", "POST" if endpoint == "graphql" else "GET" if payload is None else "PATCH"]
    if payload is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=None if payload is None else rendered(payload),
                            text=True, capture_output=True, timeout=30)
    # Do not echo gh stderr or credentials into reports; failed requests are not
    # treated as empty policy or green check evidence.
    require(result.returncode == 0, f"GitHub API request failed (exit {result.returncode}); inspect gh authentication/network locally")
    return decode(result.stdout)


def live():
    require(api(f"repos/{REPOSITORY}/rulesets") == [], "repository/inherited rulesets appeared; reconcile before proceeding")
    graph = api("graphql", {"query": RULE_QUERY})
    fields(graph, {"data"}, "GraphQL response")
    fields(graph["data"], {"repository"}, "GraphQL data")
    repository = graph["data"]["repository"]
    fields(repository, {"ref"}, "GraphQL repository")
    fields(repository["ref"], {"branchProtectionRule"}, "GraphQL ref")
    return normalize(api(ENDPOINT), repository["ref"]["branchProtectionRule"])


def additions(current, desired):
    require(current["classic_rule"] == desired["classic_rule"] and current["rulesets"] == desired["rulesets"],
            "apply must preserve classic rule and rulesets policy")
    before, after = current["protection"], desired["protection"]
    require({key: value for key, value in before.items() if key != "required_status_checks"} ==
            {key: value for key, value in after.items() if key != "required_status_checks"},
            "apply only adds status checks; non-status policy must be preserved")
    old, new = before["required_status_checks"], after["required_status_checks"]
    require(old["strict"] == new["strict"], "apply must preserve strict checking")
    prior = {check["context"]: check["app_id"] for check in old["checks"]}
    future = {check["context"]: check["app_id"] for check in new["checks"]}
    require(all(future.get(name) == app for name, app in prior.items()), "apply must preserve every existing check and source-app binding")
    return [check for check in new["checks"] if check["context"] not in prior]


def verify_green(sha, added):
    require(re.fullmatch(r"[0-9a-f]{40}", sha or "") is not None, "apply requires a full lowercase --verified-sha")
    if not added:
        return
    response = api(f"repos/{REPOSITORY}/commits/{sha}/check-runs?per_page=100")
    require(type(response) is dict and type(response.get("total_count")) is int and
            0 <= response["total_count"] <= 100 and type(response.get("check_runs")) is list and
            len(response["check_runs"]) == response["total_count"], "incomplete check-run evidence; refuse pagination/truncation")
    for check in added:
        matching = [run for run in response["check_runs"] if type(run) is dict and run.get("name") == check["context"]]
        require(len(matching) == 1, f"new check needs exactly one remote run: {check['context']}")
        run = matching[0]
        require(run.get("head_sha") == sha and run.get("status") == "completed" and
                run.get("conclusion") == "success" and type(run.get("app")) is dict and
                type(run["app"].get("id")) is int and run["app"]["id"] == check["app_id"],
                f"new check lacks remote green with the required app binding: {check['context']}")


def apply(desired, expected, sha):
    require(not any(name in os.environ for name in ("CI", "GITHUB_ACTIONS", "GITHUB_RUN_ID", "RUNNER_ENVIRONMENT")),
            "apply is local-maintainer-only; refuse CI environment")
    current = live()
    require(current == expected, "unexpected live-policy drift; reconcile the expected-current snapshot before apply")
    added = additions(current, desired)
    verify_green(sha, added)
    require(live() == expected, "live-policy drift immediately before write; refusing apply")
    if current == desired:
        return "PASS: live policy matches; no write needed"
    api(ENDPOINT + "/required_status_checks", desired["protection"]["required_status_checks"])
    require(live() == desired, "post-apply read-back differs; inspect live policy before any further action (no automatic rollback)")
    return "PASS: additive required checks applied; complete policy read-back matches"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("export", help="read-only canonical live JSON on stdout", allow_abbrev=False)
    check = sub.add_parser("check", help="read-only complete-policy comparison", allow_abbrev=False)
    check.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    writer = sub.add_parser("apply", help="explicit local additive-check apply", allow_abbrev=False)
    writer.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    writer.add_argument("--expected-current", type=Path, required=True)
    writer.add_argument("--verified-sha", required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "export":
            print(rendered(live()), end="")
        elif args.mode == "check":
            desired, current = read_definition(args.definition), live()
            if desired != current:
                print("".join(difflib.unified_diff(rendered(desired).splitlines(True), rendered(current).splitlines(True),
                                                 fromfile="definition", tofile="live")), end="")
                return 1
            print("PASS: complete live policy matches the definition")
        else:
            print(apply(read_definition(args.definition), read_definition(args.expected_current), args.verified_sha))
        return 0
    except (PolicyError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
