# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| Latest release | Yes |
| Older releases and unreleased forks | No |

## Local behavior and data handling

Role2Reel is an instruction and template package. Its bundled Python scripts make no network requests. YAML templates and YAML-capable production audits use the declared PyYAML dependency; initialization, packaging, dialogue auditing, and CSV/JSON storyboard timing checks otherwise use the standard library. The initializer writes a project tree at the target path and does not overwrite existing files unless `--force` is supplied. The packager writes or replaces `dist/role2reel.zip` by default, or the exact path supplied with `--output`. The audit and repository-validation scripts read local files and print findings.

Using the skill through Codex or sending its output to a video, model, storage, or collaboration provider is separate from those local scripts. That processing is governed by the selected services and their data controls. Remove confidential scripts, personal data, faces, voices, credentials, local paths, and unreleased assets unless you are authorized to share them.

## Report a vulnerability

Use GitHub's private security advisory feature for this repository. Do not include vulnerability details or real production material in a public issue. If the private form is unavailable, open a [security contact request](https://github.com/niuyupeng/role2reel/issues/new?template=security-contact.yml) with no sensitive details; a maintainer will restore a private reporting route.

We aim to acknowledge a report within five business days and provide an initial status update within fourteen calendar days. Timelines for a fix or disclosure depend on severity and coordination needs.
