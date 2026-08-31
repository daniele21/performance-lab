#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const [reportPath, ...requiredJourneys] = process.argv.slice(2);
if (!reportPath || requiredJourneys.length === 0) {
  console.error(
    "usage: verify-e2e-media.mjs <playwright-report.json> <journey-id>...",
  );
  process.exit(2);
}

const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
const specs = [];

function walkSuite(suite, parents = []) {
  const nextParents = suite.title ? [...parents, suite.title] : parents;
  for (const spec of suite.specs ?? []) {
    specs.push({
      ...spec,
      fullTitle: [...nextParents, spec.title].filter(Boolean).join(" "),
    });
  }
  for (const child of suite.suites ?? []) {
    walkSuite(child, nextParents);
  }
}

function attachmentExists(attachment) {
  if (!attachment.path) {
    return false;
  }
  if (path.isAbsolute(attachment.path)) {
    return fs.existsSync(attachment.path);
  }
  return [
    path.resolve(attachment.path),
    path.resolve(path.dirname(reportPath), attachment.path),
  ].some((candidate) => fs.existsSync(candidate));
}

for (const suite of report.suites ?? []) {
  walkSuite(suite);
}

const errors = [];
for (const journey of requiredJourneys) {
  const escapedJourney = journey.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matcher = new RegExp(
    `(^|[^A-Z0-9])${escapedJourney}(?=$|[^0-9])`,
    "i",
  );
  const candidates = specs.filter((spec) => matcher.test(spec.fullTitle));
  const passedResults = candidates.flatMap((spec) =>
    (spec.tests ?? []).flatMap((test) =>
      (test.results ?? [])
        .filter((result) => result.status === "passed")
        .map((result) => ({ spec, result })),
    ),
  );

  if (passedResults.length === 0) {
    errors.push(
      `${journey}: no passing Playwright result mapped to this critical journey`,
    );
    continue;
  }

  const hasScreenshot = passedResults.some(({ result }) =>
    (result.attachments ?? []).some(
      (attachment) =>
        attachment.contentType === "image/png" && attachmentExists(attachment),
    ),
  );
  const hasVideo = passedResults.some(({ result }) =>
    (result.attachments ?? []).some(
      (attachment) =>
        attachment.contentType?.startsWith("video/") &&
        attachmentExists(attachment),
    ),
  );

  if (!hasScreenshot) {
    errors.push(`${journey}: missing screenshot artifact on passing E2E evidence`);
  }
  if (!hasVideo) {
    errors.push(`${journey}: missing video artifact on passing E2E evidence`);
  }
}

if (errors.length) {
  console.error("E2E media evidence check: FAIL");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`E2E media evidence check: PASS (${requiredJourneys.join(", ")})`);
console.log(`report=${path.resolve(reportPath)}`);
