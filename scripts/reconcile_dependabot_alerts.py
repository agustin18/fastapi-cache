# The utility also supports Python 3.8; retain typing.Dict/List/Optional annotations.
# ruff: noqa: UP006, UP045
"""Capture current GitHub alerts and reconcile them with the immutable GHSA history."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    cast,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPOSITORY = "agustin18/fastapi-cache"
SECURITY_EVIDENCE_DIR = REPOSITORY_ROOT / "audit" / "security"
HISTORICAL_SNAPSHOT = SECURITY_EVIDENCE_DIR / "DEPENDABOT_ALERTS_2026-11-16.csv"

PRELIMINARY_DISPOSITIONS: Dict[str, Dict[str, str]] = {
    "GHSA-82r6-8w77-94w6": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "maintainer_decision": (
            "ACCEPTED_RISK_LEGACY_RUNTIME_AND_ISOLATED_TEST_LOCK_PROFILE"
        ),
        "profile_scope": (
            "Python 3.8/3.9 runtime and Poetry-installed test profiles use AnyIO 4.5.2. The "
            "maintainer accepts the runtime residual as separately scoped and accepts the Poetry "
            "test residual only in isolated test environments; tests use in-process ASGI clients "
            "and local services and must not direct AnyIO TLS to attacker-controlled IDN hosts or "
            "untrusted external endpoints. This is not a security claim for consumer applications "
            "or arbitrary legacy deployments."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#approved-release-gates-and-maintainer-decisions"
        ),
        "remaining_action": (
            "Keep legacy tests on in-process ASGI clients and local services; reassess this "
            "acceptance if tests introduce untrusted external hosts or endpoints. Verify modern "
            "lock profiles remain on AnyIO >=4.14.2."
        ),
        "release_gate": "RC: preserve isolated legacy test-profile boundary",
    },
    "GHSA-5p39-cfhj-2xmp": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires an AnyIO process-pool worker to write enough data to stderr; "
            "fastapi_cache does not start process-pool workers. Consumer process use "
            "is outside this package-path assessment."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-f96h-pmfr-66vw": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Reachable when a consuming FastAPI app parses attacker-controlled "
            "multipart form data with Starlette; fastapi_cache contains no form parser."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-2c2j-9gv5-cj73": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires a consuming Starlette app to parse large attacker-controlled "
            "multipart uploads; fastapi_cache does not handle request forms or files."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-82w8-qh3p-5jfq": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires a consuming app to parse attacker-controlled URL-encoded form "
            "data through Starlette request.form(); no such call exists in fastapi_cache."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-86qp-5c8j-p5mr": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Relevant only when consumer security decisions depend on request.url.path; "
            "fastapi_cache's key builder does not read request URL fields."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-jp82-jpqv-5vv3": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires a malformed request target and consumer middleware/application "
            "trusting reconstructed URL authority; the package key builder ignores it."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-x746-7m8f-x49c": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires a consumer route based on Starlette HTTPEndpoint method dispatch; "
            "fastapi_cache does not define or dispatch such endpoints."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Complete individual profile/reachability disposition before RC.",
        "release_gate": "RC",
    },
    "GHSA-wqp7-x3pw-xc5r": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Windows-only risk in the example's Starlette StaticFiles route; not a core "
            "cache API path. Consumers serving static files need separate review."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Bound the Windows/example deployment scope before RC.",
        "release_gate": "RC",
    },
    "GHSA-cq5v-8q36-5273": {
        "preliminary_disposition": "EXPERIMENTAL_EXTRA",
        "maintainer_decision": "PENDING_EXACT_RC_ARTIFACT_EVIDENCE",
        "profile_scope": (
            "The target stable DynamoDB extra is restricted to Python >=3.10 and aiohttp "
            ">=3.14.4; Python 3.8/3.9 omit aiobotocore/aiohttp. This exceeds the parser fix "
            "version; focused external review confirmed the markers and lock resolutions, and "
            "locked-profile CI passed the loopback transport smoke. Exact RC artifact evidence "
            "remains pending."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#approved-release-gates-and-maintainer-decisions"
        ),
        "remaining_action": (
            "Archive the uniquely versioned RC wheel, metadata, installed-package inventory and "
            "complete pip-audit output; compare it with the TestPyPI wheel before re-evaluating."
        ),
        "release_gate": "RC: verify exact DynamoDB profile artifact",
    },
    "GHSA-h4cc-hm5h-fmm9": {
        "preliminary_disposition": "NOT_APPLICABLE",
        "maintainer_decision": "BOUNDED_TO_DEFAULT_DYNAMODB_TRANSPORT",
        "profile_scope": "Default aiobotocore transport only; custom transports and independent aiohttp use excluded",
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Retain transport boundary and reassess any custom transport change.",
        "release_gate": "Stable boundary review",
    },
    "GHSA-8988-9cw3-xx77": {
        "preliminary_disposition": "NOT_APPLICABLE",
        "profile_scope": "Default DynamoDB transport only; independent urllib3 use excluded",
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Keep applicability bounded to the inspected transport.",
        "release_gate": "Stable boundary review",
    },
    "GHSA-vxq7-64xx-v4gw": {
        "preliminary_disposition": "NOT_APPLICABLE",
        "profile_scope": "Default DynamoDB transport only; independent urllib3 use excluded",
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Keep applicability bounded to the inspected transport.",
        "release_gate": "Stable boundary review",
    },
    "GHSA-5239-wwwm-4pmq": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires running Pygments AdlLexer on crafted source; fastapi_cache does "
            "not import Pygments or invoke lexers. Consumer tooling use is separate."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Screen consumer/tool profiles for direct lexer use before stable.",
        "release_gate": "Stable screening",
    },
    "GHSA-mf9w-mj56-hr94": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires python-dotenv set_key/unset_key on an attacker-controlled symlink "
            "and a cross-device rename fallback; the package does not mutate dotenv files."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Screen deployment/tool scripts for dotenv mutation before stable.",
        "release_gate": "Stable screening",
    },
    "GHSA-65pc-fj4g-8rjx": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            "Requires idna.encode() on a very long attacker-controlled hostname; "
            "fastapi_cache uses configured DynamoDB regions, not request-supplied hosts."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#source-verified-preliminary-code-path-dispositions"
        ),
        "remaining_action": "Screen custom endpoints and untrusted hostname use before stable.",
        "release_gate": "Stable screening",
    },
}

_AIOHTTP_NON_REACHABLE_TRIGGERS = {
    "GHSA-6mq8-rvhq-8wgg": "compressed inbound request parsing on an aiohttp server",
    "GHSA-2g87-pp6c-29x5": "WebSocket frame reassembly on a client or server",
    "GHSA-5wr8-gcqf-gqf3": "initial request/header timeout on an aiohttp server",
    "GHSA-9xw5-w5jj-pvcg": "multipart Request.post() handling on an aiohttp server",
    "GHSA-5rmc-48h2-hvcm": "WebSocket receive-queue processing on a client or server",
    "GHSA-28qf-cpwq-vmc2": "the pure-Python aiohttp server parser behind a declined upgrade",
    "GHSA-pw86-h8fm-j323": "unbounded request buffering during an aiohttp server upgrade",
    "GHSA-3rp8-rxj8-mvjw": "WebSocket max_msg_size processing on a client or server",
    "GHSA-24c4-3p7v-29cm": "multipart BodyPartReader handling on an aiohttp server",
    "GHSA-xgw8-8ccx-rmqh": "URL-encoded Request.post() parsing on an aiohttp server",
    "GHSA-jm3w-gw2p-xjfj": "Application.add_domain() host matching on an aiohttp server",
}

for _ghsa_id, _trigger in _AIOHTTP_NON_REACHABLE_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "NOT_APPLICABLE",
        "profile_scope": (
            f"Affected trigger: {_trigger}. DynamoBackend uses aiobotocore's HTTP client; "
            "this package does not create aiohttp servers or WebSocket clients. "
            "Independent consumer aiohttp use is outside this package-path assessment."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#aiohttp-client-path-review"
        ),
        "remaining_action": (
            "Reassess if the backend adds the affected server/WebSocket API; screen "
            "independent consumer aiohttp use separately."
        ),
        "release_gate": "RC: confirm package-path boundary",
    }

_URLLIB3_NON_REACHABLE_TRIGGERS = {
    "GHSA-gm62-xv2j-4w53": "chained response decompression",
    "GHSA-2xpw-w6gg-jr37": "streaming decompression of highly compressed responses",
    "GHSA-38jv-5279-wg99": "streaming decompression across redirects",
    "GHSA-qccp-gfcp-xxvc": "sensitive headers on proxied low-level redirects",
}

for _ghsa_id, _trigger in _URLLIB3_NON_REACHABLE_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "NOT_APPLICABLE",
        "profile_scope": (
            f"Affected trigger: {_trigger}. The package's DynamoDB backend uses "
            "aiobotocore/aiohttp and calls no urllib3 API; requests is a development "
            "dependency. Independent consumer urllib3 use is outside this assessment."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#urllib3-transitive-path-review"
        ),
        "remaining_action": (
            "Reassess if package code adds urllib3 calls; screen independent consumer "
            "urllib3 usage separately."
        ),
        "release_gate": "RC: confirm package-path boundary",
    }

_MULTIPART_APPLICATION_TRIGGERS = {
    "GHSA-59g5-xgcq-4qw3": "large preamble/trailing data around multipart boundaries",
    "GHSA-wp53-j4wj-2cfg": (
        "path traversal only with UPLOAD_DIR and UPLOAD_KEEP_FILENAME=True"
    ),
    "GHSA-pp6c-gr5w-3c5g": "unbounded multipart part-header parsing",
    "GHSA-5rvq-cxj2-64vf": "quadratic URL-encoded form parsing with semicolon separators",
}

for _ghsa_id, _trigger in _MULTIPART_APPLICATION_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            f"Affected trigger: {_trigger}. Reachable when a FastAPI consumer parses "
            "untrusted form data; fastapi_cache contains no form-parser call."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#python-multipart-consumer-form-boundary"
        ),
        "remaining_action": (
            "Verify the consumer form surface and selected dependency version; this "
            "preliminary classification is not risk acceptance."
        ),
        "release_gate": "RC: verify dependency/profile and form reachability",
    }

_CRYPTOGRAPHY_DEVELOPMENT_TRIGGERS = {
    "GHSA-r6ph-v2qm-q3c2": "unvalidated SECT-curve public-key points",
    "GHSA-537c-gmf6-5ccf": "vulnerable OpenSSL bundled in cryptography wheels",
    "GHSA-jwv3-5hgf-82ww": "pathological certificate-chain construction",
}

for _ghsa_id, _trigger in _CRYPTOGRAPHY_DEVELOPMENT_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "DEVELOPMENT_ONLY",
        "profile_scope": (
            f"Affected trigger: {_trigger}. The lock path is optional linting "
            "types-redis -> cryptography; cryptography is not a fastapi_cache runtime import."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#cryptography-development-only-boundary"
        ),
        "remaining_action": (
            "Keep the runtime-wheel boundary verified and track the Poetry linting "
            "environment separately."
        ),
        "release_gate": "RC: confirm runtime-wheel boundary",
    }

_DNSPYTHON_APPLICATION_TRIGGERS = {
    "GHSA-45c3-73f7-pv4m": (
        "processing attacker-controlled DNS wire responses with dnspython"
    ),
    "GHSA-vvf4-9x63-8xvv": "parsing attacker-controlled DNS zone text containing WKS records",
}

for _ghsa_id, _trigger in _DNSPYTHON_APPLICATION_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            f"Affected trigger: {_trigger}. dnspython is transitive through "
            "email-validator; fastapi_cache contains no DNS validation or zone parsing."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#dnspython-consumer-boundary"
        ),
        "remaining_action": (
            "Verify any package-controlled DNS path remains absent; consumer code using "
            "dnspython APIs needs separate review."
        ),
        "release_gate": "RC: verify package and consumer profile boundary",
    }

_AIOHTTP_MEDIUM_LOW_NON_REACHABLE_TRIGGERS = {
    "GHSA-8495-4g3g-x7pr": "pure-Python server request parsing of chunk extensions",
    "GHSA-9548-qrrj-x5pj": "pure-Python server parsing of chunked request trailers",
    "GHSA-69f9-5gxw-wvc2": "pure-Python server parsing of non-ASCII header values",
    "GHSA-mqqc-3gqh-h2x8": "server parsing of non-ASCII Range-header digits",
    "GHSA-54jq-c3m8-4m76": "aiohttp static-file path handling",
    "GHSA-jj3x-wxrx-4x23": "optimized aiohttp server POST-body parsing",
    "GHSA-6jhg-hg63-jvvf": "aiohttp server Request.post() body handling",
    "GHSA-g84x-mcqj-x9qq": "aiohttp server Request.read() chunk parsing",
    "GHSA-fh55-r93g-j68g": "aiohttp server Request.cookies parsing",
    "GHSA-2vrm-gr82-f7m5": "constructing outbound multipart headers from untrusted content types",
    "GHSA-p998-jp59-783m": "aiohttp Windows static-resource handling",
    "GHSA-m5qp-6w8w-w647": "reading multipart response headers",
    "GHSA-3wq7-rqq7-wx6j": "aiohttp server Request.post() multipart field handling",
    "GHSA-mwh4-6h8g-pg8w": "constructing aiohttp server responses from an untrusted reason phrase",
    "GHSA-63hf-3vf5-4wqf": "aiohttp C-parser handling of inbound request headers",
    "GHSA-c427-h43c-vf67": "aiohttp server handling of duplicate Host headers",
    "GHSA-jg22-mg44-37j8": "loading untrusted serialized aiohttp CookieJar data",
    "GHSA-hg6j-4rv6-33pg": "passing per-request cookies to aiohttp requests",
    "GHSA-m6qw-4cw2-hm4m": "constructing outbound multipart headers from untrusted values",
    "GHSA-2fqr-mr3j-6wp8": "saving and restoring aiohttp CookieJar state",
    "GHSA-hpj7-wq8m-9hgp": "using aiohttp DigestAuthMiddleware across redirects",
    "GHSA-63hw-fmq6-xxg2": "aiohttp C-parser handling of inbound request lines",
    "GHSA-g3cq-j2xw-wf74": "aiohttp server cleanup of unread compressed request bodies",
    "GHSA-4fvr-rgm6-gqmc": "aiohttp server queuing of pipelined requests",
    "GHSA-9x8q-7h8h-wcw9": "writing aiohttp server responses after a client disconnect",
    "GHSA-4m7w-qmgq-4wj5": "overriding server_hostname on individual aiohttp requests",
    "GHSA-xcgm-r5h9-7989": "aiohttp server WebSocket frame handling",
    "GHSA-mq44-7p77-q5h7": "aiohttp WebSocket client decompression",
    "GHSA-mfx4-hv73-q22v": "aiohttp server WebSocket-upgrade request parsing",
    "GHSA-pqxq-w44r-73xw": "pure-Python aiohttp server request parsing",
    "GHSA-f9xw-jh8m-3mwq": "aiohttp server interpretation of absolute-form request targets",
}

for _ghsa_id, _trigger in _AIOHTTP_MEDIUM_LOW_NON_REACHABLE_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "NOT_APPLICABLE",
        "profile_scope": (
            f"Affected trigger: {_trigger}. The optional DynamoBackend uses "
            "aiobotocore's HTTP client and does not call this aiohttp API; independent "
            "consumer aiohttp use is outside this package-path screen."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#aiohttp-medium-low-screen"
        ),
        "remaining_action": (
            "Retain this API boundary and reassess if package code adopts the affected "
            "aiohttp server/client feature."
        ),
        "release_gate": "Stable: reconcile row",
    }

_AIOHTTP_MEDIUM_LOW_CLIENT_REVIEW_TRIGGERS = {
    "GHSA-w2fm-2cpv-w7v5": "attacker-controlled response trailer headers can consume memory",
    "GHSA-966j-vmvw-g2g9": (
        "cross-origin redirects can retain Cookie and Proxy-Authorization headers"
    ),
    "GHSA-494j-54xm-rwp3": "Secure cookie attributes may not be enforced for shared cookies",
    "GHSA-6cjc-53gc-5rqm": "malicious Max-Age cookie values may exhaust the connector pool",
    "GHSA-gx76-c99x-2c96": "a subdomain cookie can widen an existing host-only cookie scope",
    "GHSA-5pv8-vvhc-h7jv": "a malicious server can grow the client CookieJar without bound",
}

for _ghsa_id, _trigger in _AIOHTTP_MEDIUM_LOW_CLIENT_REVIEW_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "EXPERIMENTAL_EXTRA",
        "maintainer_decision": "PENDING_EXACT_RC_ARTIFACT_EVIDENCE",
        "profile_scope": (
            f"Affected trigger: {_trigger}. The target stable DynamoDB extra is restricted "
            "to Python >=3.10 with aiohttp >=3.14.4, which includes the advisory fix; the "
            "client extra is absent on Python 3.8/3.9. Focused external review confirmed the "
            "markers and lock floor; locked-profile CI passed the loopback transport smoke. "
            "Exact RC artifact evidence remains pending."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#aiohttp-medium-low-client-paths"
        ),
        "remaining_action": (
            "Archive the exact RC wheel, metadata, installed-package inventory and pip-audit "
            "output; compare it with the TestPyPI wheel before re-evaluating this row."
        ),
        "release_gate": "RC: verify exact DynamoDB profile artifact",
    }

PRELIMINARY_DISPOSITIONS["GHSA-hcc4-c3v8-rx92"] = {
    "preliminary_disposition": "EXPERIMENTAL_EXTRA",
    "maintainer_decision": "PENDING_STABLE_PATCHED_PROFILE_VERIFICATION",
    "profile_scope": (
        "The optional DynamoBackend uses an aiohttp TCPConnector through aiobotocore. The "
        "target stable extra is restricted to Python >=3.10 and aiohttp >=3.14.4, beyond "
        "this advisory's fix; Python 3.8/3.9 omit the client dependencies. The patched profile "
        "still needs candidate artifact verification."
    ),
    "evidence_reference": (
        "SECURITY_DEPENDENCY_INVENTORY.md#aiohttp-medium-low-client-paths"
    ),
    "remaining_action": (
        "Verify the aiohttp floor and legacy extra exclusion in the exact RC wheel; then close "
        "the stable-stage boundary using the documented single-endpoint scope. Focused profile "
        "review is complete."
    ),
    "release_gate": "Stable: verify optional DynamoDB DNS cache scope",
}

_JINJA2_APPLICATION_TRIGGERS = {
    "GHSA-q2x7-8rv6-6q7h": "sandboxed templates containing attacker-controlled content",
    "GHSA-gmj6-6f8f-6699": "templates whose content and filename are attacker-controlled",
    "GHSA-cpwx-vrp4-4pq7": "sandboxed templates using the attr filter to reach format",
}

for _ghsa_id, _trigger in _JINJA2_APPLICATION_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            f"Affected trigger: {_trigger}. fastapi_cache does not render or compile "
            "templates; consumer-owned template rendering is outside the package path."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#jinja2-consumer-template-boundary"
        ),
        "remaining_action": (
            "Review consumer template sources and rendering separately; keep the cache "
            "package's non-rendering boundary."
        ),
        "release_gate": "Stable: reconcile row",
    }

_PYTHON_MULTIPART_MEDIUM_LOW_TRIGGERS = {
    "GHSA-mj87-hwqh-73pj": "large multipart preamble or epilogue data",
    "GHSA-vffw-93wf-4j4q": "Content-Disposition extended-parameter smuggling",
    "GHSA-6jv3-5f52-599m": "semicolon separators changing URL-encoded form parameters",
    "GHSA-v9pg-7xvm-68hf": "negative Content-Length causing parse_form() to read to EOF",
}

for _ghsa_id, _trigger in _PYTHON_MULTIPART_MEDIUM_LOW_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "profile_scope": (
            f"Affected trigger: {_trigger}. The package contains no form or upload "
            "parser call; a consuming application must parse attacker-controlled forms."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#python-multipart-consumer-form-boundary"
        ),
        "remaining_action": (
            "Review consumer forms, upload configuration and selected parser version; "
            "this preliminary label is not risk acceptance."
        ),
        "release_gate": "Stable: reconcile row",
    }

_CRYPTOGRAPHY_DEVELOPMENT_TRIGGERS = {
    "GHSA-h4gh-qq45-vh27": "vulnerable OpenSSL bundled in cryptography wheels",
    "GHSA-79v4-65xg-pq4g": "vulnerable OpenSSL bundled in cryptography wheels",
    "GHSA-m959-cc7f-wv43": "incomplete DNS name-constraint enforcement",
}

for _ghsa_id, _trigger in _CRYPTOGRAPHY_DEVELOPMENT_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "DEVELOPMENT_ONLY",
        "profile_scope": (
            f"Affected trigger: {_trigger}. The lock path is optional linting "
            "types-redis -> cryptography; cryptography is not a package runtime import."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#cryptography-development-only-boundary"
        ),
        "remaining_action": (
            "Keep the runtime-wheel boundary verified and reconcile the locked "
            "development environment separately."
        ),
        "release_gate": "Stable: reconcile development row",
    }

PRELIMINARY_DISPOSITIONS["GHSA-6w46-j5rx-g56g"] = {
    "preliminary_disposition": "DEVELOPMENT_ONLY",
    "profile_scope": (
        "The affected surface is pytest temporary-directory handling under shared "
        "Unix /tmp; pytest is a development dependency, not part of the package wheel."
    ),
    "evidence_reference": (
        "SECURITY_DEPENDENCY_INVENTORY.md#development-tooling-boundary"
    ),
    "remaining_action": "Reconcile the locked test-tool environment separately.",
    "release_gate": "Stable: reconcile development row",
}

_REQUESTS_DEVELOPMENT_TRIGGERS = {
    "GHSA-9hjg-9r4m-mvj7": "malicious URLs causing .netrc credential leakage",
    "GHSA-gc5v-m9x4-r6x2": "predictable temporary-file reuse in extract_zipped_paths()",
}

for _ghsa_id, _trigger in _REQUESTS_DEVELOPMENT_TRIGGERS.items():
    PRELIMINARY_DISPOSITIONS[_ghsa_id] = {
        "preliminary_disposition": "DEVELOPMENT_ONLY",
        "profile_scope": (
            f"Affected trigger: {_trigger}. requests is a development dependency and "
            "is not imported by fastapi_cache runtime source."
        ),
        "evidence_reference": (
            "SECURITY_DEPENDENCY_INVENTORY.md#development-tooling-boundary"
        ),
        "remaining_action": "Reconcile the locked development/test tooling profile separately.",
        "release_gate": "Stable: reconcile development row",
    }

PRELIMINARY_DISPOSITIONS["GHSA-pq67-6m6q-mj2v"] = {
    "preliminary_disposition": "NOT_APPLICABLE",
    "profile_scope": (
        "urllib3 is runtime/transitive through botocore in the optional DynamoDB graph, "
        "but this advisory requires constructing PoolManager with a specific retry "
        "configuration. fastapi_cache delegates to aiobotocore/aiohttp and does not call "
        "that API; default botocore/requests configurations are not affected."
    ),
    "evidence_reference": (
        "SECURITY_DEPENDENCY_INVENTORY.md#urllib3-transitive-path-review"
    ),
    "remaining_action": (
        "Keep this disposition limited to the inspected optional transport; screen "
        "independent consumer urllib3 PoolManager use separately."
    ),
    "release_gate": "Stable: verify transitive runtime path",
}

FIXED_DISPOSITIONS = {
    "GHSA-vqfr-h8mv-ghfj": {
        "preliminary_disposition": "FIXED",
        "triage_status": "FIXED",
        "maintainer_decision": "FIXED_BY_PR_25_LOCK_UPDATE",
        "profile_scope": "h11 lock resolution to 0.16.0; verify the selected runtime profiles",
        "evidence_reference": "poetry.lock; PR #25; current Dependabot state fixed",
        "remaining_action": "Keep the patched resolution in the lock and wheel profiles.",
        "release_gate": "Closed for this historical row",
    }
}

CURRENT_ONLY_DISPOSITIONS: Dict[str, Dict[str, str]] = {
    "GHSA-7f5h-v6xp-fcq8": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "maintainer_decision": "PENDING_CURRENT_SNAPSHOT_AND_LEGACY_REACHABILITY_REVIEW",
        "profile_scope": (
            "Starlette 0.39.0 through 0.49.0 FileResponse Range parsing may "
            "allow unauthenticated CPU exhaustion. The Python 3.8/3.9 lock "
            "includes Starlette 0.44.0; modern locked profiles are patched. "
            "fastapi_cache does not construct FileResponse/StaticFiles, and "
            "the unused StaticFiles(directory='.') mount has been removed "
            "from the Redis example. Consumers may independently serve files."
        ),
        "evidence_reference": (
            "https://github.com/Kludex/starlette/security/advisories/"
            "GHSA-7f5h-v6xp-fcq8"
        ),
        "remaining_action": (
            "Capture current Dependabot state into a NEW snapshot, verify the "
            "selected Python 3.8/3.9 and modern lock profiles, and record the "
            "advisory in the generated triage register. Confirm no "
            "FileResponse/StaticFiles path is reachable from the library "
            "or its examples. Do not mark the consumer-owned vulnerability fixed."
        ),
        "release_gate": "Before RC2: example fix; stable: final GHSA disposition",
    },
    "GHSA-48p4-8xcf-vxj5": {
        "preliminary_disposition": "APPLICATION_CONDITIONAL",
        "maintainer_decision": "PYODIDE_OUTSIDE_VERIFIED_SUPPORT_SCOPE",
        "profile_scope": (
            "The advisory affects urllib3 redirect handling in Pyodide browser/Node runtimes. "
            "Compatibility and security guarantees cover the tested server-side CPython matrix; "
            "Pyodide, browser and Node runtimes are not validated or covered. This is not evidence "
            "of functional incompatibility. fastapi_cache calls no urllib3 API; DynamoDB uses "
            "aiobotocore/aiohttp. Consumer-owned Pyodide use remains separate."
        ),
        "evidence_reference": (
            "https://github.com/advisories/GHSA-48p4-8xcf-vxj5"
        ),
        "remaining_action": (
            "Keep Pyodide/browser/Node outside the verified support matrix; consumer-owned urllib3 "
            "use remains separate. Leave final triage pending."
        ),
        "release_gate": "Stable: final current-only GHSA triage",
    }
}

HISTORICAL_FIELDS = [
    "alert_number",
    "ghsa_id",
    "cve_id",
    "severity",
    "package",
    "lock_versions",
    "lock_python_versions",
    "lock_optional",
    "manifest",
    "scope",
    "relationship",
    "vulnerable_version_range",
    "first_patched_version",
    "triage_status",
]

CURRENT_SNAPSHOT_FIELDS = [
    "snapshot_date",
    "snapshot_id",
    "alert_number",
    "state",
    "ghsa_id",
    "cve_id",
    "severity",
    "summary",
    "package",
    "manifest_path",
    "scope",
    "relationship",
    "vulnerable_version_range",
    "first_patched_version",
    "created_at",
    "fixed_at",
    "dismissed_at",
    "dismissed_reason",
]

TRIAGE_FIELDS = [
    "historical_alert_number",
    "ghsa_id",
    "cve_id",
    "historical_severity",
    "historical_package",
    "lock_versions",
    "lock_python_versions",
    "lock_optional",
    "manifest",
    "scope",
    "relationship",
    "vulnerable_version_range",
    "historical_first_patched_version",
    "historical_triage_status",
    "snapshot_date",
    "current_snapshot_id",
    "current_alert_number",
    "current_state",
    "current_severity",
    "current_package",
    "current_manifest",
    "current_vulnerable_version_range",
    "current_first_patched_version",
    "preliminary_disposition",
    "triage_status",
    "maintainer_decision",
    "profile_scope",
    "evidence_reference",
    "remaining_action",
    "release_gate",
    "manual_override_fields",
]

MANUAL_OVERRIDEABLE_FIELDS = [
    "preliminary_disposition",
    "maintainer_decision",
    "profile_scope",
    "evidence_reference",
    "remaining_action",
    "release_gate",
]

MANUAL_OVERRIDE_SEPARATOR = ";"


def _get_manual_override_fields(
    row: Mapping[str, str], ghsa_id: str, current_state: str
) -> Set[str]:
    marker = row.get("manual_override_fields", "")
    if not marker.strip():
        return set()
    fields = [
        field.strip() for field in marker.split(MANUAL_OVERRIDE_SEPARATOR)
    ]
    if any(not field for field in fields):
        raise ValueError(f"empty manual override field name for {ghsa_id}")
    if len(fields) != len(set(fields)):
        raise ValueError(f"duplicate manual override field for {ghsa_id}")
    requested = set(fields)
    unknown = requested - set(MANUAL_OVERRIDEABLE_FIELDS)
    if unknown:
        raise ValueError(
            "unknown manual override field(s) for "
            f"{ghsa_id}: {', '.join(sorted(unknown))}"
        )
    missing_values = sorted(
        field for field in requested if not row.get(field, "").strip()
    )
    if missing_values:
        raise ValueError(
            "manual override field(s) have empty values for "
            f"{ghsa_id}: {', '.join(missing_values)}"
        )
    if "preliminary_disposition" in requested:
        disposition = row["preliminary_disposition"].strip()
        allowed_dispositions = {
            "APPLICATION_CONDITIONAL",
            "DEVELOPMENT_ONLY",
            "EXPERIMENTAL_EXTRA",
            "FIXED",
            "NOT_APPLICABLE",
            "PENDING",
        }
        if disposition not in allowed_dispositions:
            raise ValueError(
                f"invalid manual preliminary disposition for {ghsa_id}: {disposition}"
            )
        if disposition == "FIXED" and current_state != "fixed":
            raise ValueError(
                "manual FIXED preliminary disposition requires current state fixed: "
                + ghsa_id
            )
    return requested


def build_current_snapshot(
    alerts: Iterable[Mapping[str, Any]],
    snapshot_date: str,
    snapshot_id: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen_alert_numbers = set()
    seen_ghsa_ids = set()
    for alert in alerts:
        advisory = alert.get("security_advisory") or {}
        vulnerability = alert.get("security_vulnerability") or {}
        dependency = alert.get("dependency") or {}
        package = dependency.get("package") or {}
        first_patched = vulnerability.get("first_patched_version") or {}
        alert_number = str(alert["number"])
        if alert_number in seen_alert_numbers:
            raise ValueError("duplicate current alert number: " + alert_number)
        seen_alert_numbers.add(alert_number)
        ghsa_id = str(advisory.get("ghsa_id") or "")
        if not ghsa_id:
            raise ValueError("current alert is missing ghsa_id")
        if ghsa_id in seen_ghsa_ids:
            raise ValueError("duplicate current GHSA: " + ghsa_id)
        seen_ghsa_ids.add(ghsa_id)
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "snapshot_id": snapshot_id or snapshot_date,
                "alert_number": alert_number,
                "state": str(alert.get("state") or ""),
                "ghsa_id": ghsa_id,
                "cve_id": str(advisory.get("cve_id") or ""),
                "severity": str(vulnerability.get("severity") or ""),
                "summary": str(advisory.get("summary") or ""),
                "package": str(package.get("name") or ""),
                "manifest_path": str(dependency.get("manifest_path") or ""),
                "scope": str(dependency.get("scope") or ""),
                "relationship": str(dependency.get("relationship") or ""),
                "vulnerable_version_range": str(
                    vulnerability.get("vulnerable_version_range") or ""
                ),
                "first_patched_version": str(
                    first_patched.get("identifier") or ""
                ),
                "created_at": str(alert.get("created_at") or ""),
                "fixed_at": str(alert.get("fixed_at") or ""),
                "dismissed_at": str(alert.get("dismissed_at") or ""),
                "dismissed_reason": str(alert.get("dismissed_reason") or ""),
            }
        )
    return sorted(rows, key=lambda row: int(row["alert_number"]))


def reconcile_historical_alerts(
    historical_rows: Iterable[Mapping[str, str]],
    current_rows: Iterable[Mapping[str, str]],
    snapshot_date: str,
    existing_triage_rows: Optional[Iterable[Mapping[str, str]]] = None,
    snapshot_id: Optional[str] = None,
) -> List[Dict[str, str]]:
    current_by_ghsa: Dict[str, Mapping[str, str]] = {}
    seen_current_alert_numbers = set()
    for row in current_rows:
        ghsa_id = row.get("ghsa_id", "").strip()
        if not ghsa_id:
            raise ValueError("current row is missing ghsa_id")
        if ghsa_id in current_by_ghsa:
            raise ValueError("duplicate current GHSA: " + ghsa_id)
        alert_number = row.get("alert_number", "").strip()
        if alert_number:
            if alert_number in seen_current_alert_numbers:
                raise ValueError(
                    "duplicate current alert number: " + alert_number
                )
            seen_current_alert_numbers.add(alert_number)
        current_by_ghsa[ghsa_id] = row

    existing_by_ghsa: Dict[str, Mapping[str, str]] = {}
    for row in existing_triage_rows or []:
        ghsa_id = row.get("ghsa_id", "").strip()
        if not ghsa_id:
            raise ValueError("existing triage row is missing ghsa_id")
        if ghsa_id in existing_by_ghsa:
            raise ValueError("duplicate existing triage GHSA: " + ghsa_id)
        existing_by_ghsa[ghsa_id] = row

    historical_rows = list(historical_rows)
    seen_historical_ids = set()
    seen_historical_alert_numbers = set()
    for historical in historical_rows:
        ghsa_id = historical.get("ghsa_id", "")
        if not ghsa_id:
            raise ValueError("historical row is missing ghsa_id")
        if ghsa_id in seen_historical_ids:
            raise ValueError("duplicate historical GHSA: " + ghsa_id)
        seen_historical_ids.add(ghsa_id)
        alert_number = historical.get("alert_number", "").strip()
        if not alert_number:
            raise ValueError("historical row is missing alert_number")
        if alert_number in seen_historical_alert_numbers:
            raise ValueError(
                "duplicate historical alert number: " + alert_number
            )
        seen_historical_alert_numbers.add(alert_number)

    untriaged_open_ids = sorted(
        ghsa_id
        for ghsa_id, current in current_by_ghsa.items()
        if current.get("state") == "open"
        and ghsa_id not in seen_historical_ids
        and ghsa_id not in CURRENT_ONLY_DISPOSITIONS
    )
    if untriaged_open_ids:
        raise ValueError(
            "current open GHSA has no historical row or current-only disposition: "
            + ", ".join(untriaged_open_ids)
        )

    triage_rows: List[Dict[str, str]] = []
    for historical in historical_rows:
        ghsa_id = historical.get("ghsa_id", "")
        current = current_by_ghsa.get(ghsa_id, {})
        disposition = dict(PRELIMINARY_DISPOSITIONS.get(ghsa_id, {}))
        if "triage_status" in disposition:
            raise ValueError(
                "PRELIMINARY_DISPOSITIONS must not set triage_status: "
                + ghsa_id
            )
        if ghsa_id in FIXED_DISPOSITIONS and current.get("state") == "fixed":
            disposition.update(FIXED_DISPOSITIONS[ghsa_id])
        elif ghsa_id in FIXED_DISPOSITIONS:
            disposition.update(
                {
                    "preliminary_disposition": "FIXED_IN_PRIOR_SNAPSHOT",
                    "triage_status": "PENDING_RECHECK",
                    "maintainer_decision": "CURRENT_ALERT_REQUIRES_RECHECK",
                    "remaining_action": "GitHub does not currently report the fix; reverify the selected profile.",
                    "release_gate": "RC recheck",
                }
            )

        row = {
            "historical_alert_number": historical.get("alert_number", ""),
            "ghsa_id": ghsa_id,
            "cve_id": historical.get("cve_id", ""),
            "historical_severity": historical.get("severity", ""),
            "historical_package": historical.get("package", ""),
            "lock_versions": historical.get("lock_versions", ""),
            "lock_python_versions": historical.get("lock_python_versions", ""),
            "lock_optional": historical.get("lock_optional", ""),
            "manifest": historical.get("manifest", ""),
            "scope": historical.get("scope", ""),
            "relationship": historical.get("relationship", ""),
            "vulnerable_version_range": historical.get(
                "vulnerable_version_range", ""
            ),
            "historical_first_patched_version": historical.get(
                "first_patched_version", ""
            ),
            "historical_triage_status": historical.get("triage_status", ""),
            "snapshot_date": snapshot_date,
            "current_snapshot_id": snapshot_id or snapshot_date,
            "current_alert_number": str(current.get("alert_number", "")),
            "current_state": str(
                current.get("state", "not_in_current_snapshot")
            ),
            "current_severity": str(current.get("severity", "")),
            "current_package": str(current.get("package", "")),
            "current_manifest": str(current.get("manifest_path", "")),
            "current_vulnerable_version_range": str(
                current.get("vulnerable_version_range", "")
            ),
            "current_first_patched_version": str(
                current.get("first_patched_version", "")
            ),
            "preliminary_disposition": "PENDING",
            "triage_status": "PENDING",
            "maintainer_decision": "",
            "profile_scope": "",
            "evidence_reference": "DEPENDABOT_ALERTS_2026-11-16.csv",
            "remaining_action": "Complete individual applicability/reachability disposition.",
            "release_gate": (
                "RC: disposition individually; stable: reconcile row"
                if historical.get("severity", "").lower()
                in {"critical", "high"}
                else "RC: screen direct serious exposure; stable: reconcile row"
            ),
        }
        row.update(disposition)

        prior = existing_by_ghsa.get(ghsa_id, {})
        override_fields = _get_manual_override_fields(
            prior, ghsa_id, row["current_state"]
        )
        for field in MANUAL_OVERRIDEABLE_FIELDS:
            if field in override_fields:
                row[field] = prior[field]
        row["manual_override_fields"] = MANUAL_OVERRIDE_SEPARATOR.join(
            field
            for field in MANUAL_OVERRIDEABLE_FIELDS
            if field in override_fields
        )
        if row["triage_status"] == "FIXED" and row["current_state"] != "fixed":
            row["triage_status"] = "PENDING_RECHECK"
            row["maintainer_decision"] = "CURRENT_ALERT_REQUIRES_RECHECK"
            row["remaining_action"] = (
                "GitHub no longer reports this alert as fixed; reverify the selected profile."
            )
        triage_rows.append(row)

    current_only_ids = sorted(
        (
            ghsa_id
            for ghsa_id in current_by_ghsa
            if ghsa_id not in seen_historical_ids
            and ghsa_id in CURRENT_ONLY_DISPOSITIONS
        ),
        key=lambda ghsa_id: int(current_by_ghsa[ghsa_id]["alert_number"]),
    )
    for ghsa_id in current_only_ids:
        current = current_by_ghsa[ghsa_id]
        disposition = dict(CURRENT_ONLY_DISPOSITIONS[ghsa_id])
        if "triage_status" in disposition:
            raise ValueError(
                "CURRENT_ONLY_DISPOSITIONS must not set triage_status: "
                + ghsa_id
            )
        row = {
            "historical_alert_number": "",
            "ghsa_id": ghsa_id,
            "cve_id": str(current.get("cve_id", "")),
            "historical_severity": "",
            "historical_package": "",
            "lock_versions": "",
            "lock_python_versions": "",
            "lock_optional": "",
            "manifest": "",
            "scope": "",
            "relationship": "",
            "vulnerable_version_range": "",
            "historical_first_patched_version": "",
            "historical_triage_status": "NOT_IN_HISTORICAL_SNAPSHOT",
            "snapshot_date": snapshot_date,
            "current_snapshot_id": snapshot_id or snapshot_date,
            "current_alert_number": str(current.get("alert_number", "")),
            "current_state": str(current.get("state", "")),
            "current_severity": str(current.get("severity", "")),
            "current_package": str(current.get("package", "")),
            "current_manifest": str(current.get("manifest_path", "")),
            "current_vulnerable_version_range": str(
                current.get("vulnerable_version_range", "")
            ),
            "current_first_patched_version": str(
                current.get("first_patched_version", "")
            ),
            "preliminary_disposition": "PENDING",
            "triage_status": "PENDING",
            "maintainer_decision": "",
            "profile_scope": "",
            "evidence_reference": "",
            "remaining_action": "Complete current-only advisory review.",
            "release_gate": "RC: disposition current-only advisory",
        }
        row.update(disposition)

        prior = existing_by_ghsa.get(ghsa_id, {})
        override_fields = _get_manual_override_fields(
            prior, ghsa_id, row["current_state"]
        )
        for field in MANUAL_OVERRIDEABLE_FIELDS:
            if field in override_fields:
                row[field] = prior[field]
        row["manual_override_fields"] = MANUAL_OVERRIDE_SEPARATOR.join(
            field
            for field in MANUAL_OVERRIDEABLE_FIELDS
            if field in override_fields
        )
        triage_rows.append(row)
    return triage_rows


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def _write_csv(
    path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, str]]
) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def ensure_current_snapshot_target(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"refusing to overwrite existing snapshot {path}; use a new snapshot ID "
            "or explicitly pass --overwrite-current-snapshot"
        )


def _fetch_current_alerts(repository: str) -> List[Mapping[str, Any]]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be in owner/name form")
    gh_executable = shutil.which("gh")
    if gh_executable is None:
        raise RuntimeError(
            "GitHub CLI `gh` is required to capture current alerts"
        )
    endpoint = f"repos/{repository}/dependabot/alerts?per_page=100"
    result = subprocess.run(  # noqa: S603 -- list arguments; no shell execution
        [gh_executable, "api", "--paginate", "--slurp", endpoint],
        check=True,
        capture_output=True,
        text=True,
    )
    pages = json.loads(result.stdout)
    if pages and isinstance(pages[0], list):
        return cast(
            List[Mapping[str, Any]], [alert for page in pages for alert in page]
        )
    return cast(List[Mapping[str, Any]], pages)


def _read_existing_triage(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    return _read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--historical", type=Path, default=HISTORICAL_SNAPSHOT)
    parser.add_argument("--output-dir", type=Path, default=SECURITY_EVIDENCE_DIR)
    parser.add_argument(
        "--current-snapshot",
        type=Path,
        help="reconcile from an existing raw snapshot without contacting GitHub",
    )
    parser.add_argument(
        "--snapshot-date",
        help="UTC snapshot date in YYYY-MM-DD form (default: today for API captures)",
    )
    parser.add_argument(
        "--overwrite-current-snapshot",
        action="store_true",
        help="explicitly replace the current snapshot file if it already exists",
    )
    args = parser.parse_args()

    if args.current_snapshot is not None:
        if args.snapshot_date is not None or args.overwrite_current_snapshot:
            parser.error(
                "--current-snapshot cannot be combined with --snapshot-date or "
                "--overwrite-current-snapshot"
            )
        current_path = args.current_snapshot
        current_rows = _read_csv(current_path)
        if not current_rows:
            raise ValueError("saved current snapshot is empty: " + str(current_path))
        snapshot_date = current_rows[0].get("snapshot_date", "")
        snapshot_id = current_rows[0].get("snapshot_id", "")
        if not snapshot_date or not snapshot_id:
            raise ValueError("saved current snapshot is missing its identity fields")
        if any(
            row.get("snapshot_date") != snapshot_date
            or row.get("snapshot_id") != snapshot_id
            for row in current_rows
        ):
            raise ValueError("saved current snapshot contains mixed identities")
    else:
        snapshot_date = (
            args.snapshot_date or datetime.now(timezone.utc).date().isoformat()
        )
        snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        current_alerts = _fetch_current_alerts(args.repository)
        current_rows = build_current_snapshot(
            current_alerts, snapshot_date, snapshot_id
        )
        current_path = args.output_dir / f"DEPENDABOT_ALERTS_{snapshot_id}.csv"
        ensure_current_snapshot_target(
            current_path, overwrite=args.overwrite_current_snapshot
        )
        # Preserve the raw capture even if reconciliation stops on a new, untriaged open GHSA.
        _write_csv(current_path, CURRENT_SNAPSHOT_FIELDS, current_rows)

    historical_rows = _read_csv(args.historical)
    triage_path = args.output_dir / "SECURITY_ADVISORY_TRIAGE.csv"
    previous_triage = _read_existing_triage(triage_path)
    triage_rows = reconcile_historical_alerts(
        historical_rows,
        current_rows,
        snapshot_date,
        previous_triage,
        snapshot_id,
    )
    _write_csv(triage_path, TRIAGE_FIELDS, triage_rows)

    current_counts = Counter(row["state"] for row in current_rows)
    historical_ids = {row["ghsa_id"] for row in historical_rows}
    historical_triage_rows = [
        row for row in triage_rows if row["historical_alert_number"]
    ]
    current_open_ids = {
        row["ghsa_id"] for row in current_rows if row["state"] == "open"
    }
    current_fixed_ids = {
        row["ghsa_id"] for row in current_rows if row["state"] == "fixed"
    }
    print(
        json.dumps(
            {
                "snapshot_date": snapshot_date,
                "snapshot_id": snapshot_id,
                "current_records": len(current_rows),
                "current_state_counts": dict(current_counts),
                "historical_rows": len(historical_rows),
                "triage_rows": len(triage_rows),
                "current_only_triage_rows": sum(
                    not row["historical_alert_number"] for row in triage_rows
                ),
                "historical_current_open": sum(
                    row["current_state"] == "open" for row in historical_triage_rows
                ),
                "historical_current_fixed": sum(
                    row["current_state"] == "fixed" for row in historical_triage_rows
                ),
                "historical_not_in_current_snapshot": sum(
                    row["current_state"] == "not_in_current_snapshot"
                    for row in historical_triage_rows
                ),
                "current_open_not_historical": len(
                    current_open_ids - historical_ids
                ),
                "current_fixed_not_historical": len(
                    current_fixed_ids - historical_ids
                ),
                "triage_state_counts": dict(
                    Counter(row["triage_status"] for row in triage_rows)
                ),
                "preliminary_disposition_counts": dict(
                    Counter(
                        row["preliminary_disposition"] for row in triage_rows
                    )
                ),
                "current_snapshot_file": str(current_path),
                "triage_register_file": str(triage_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
