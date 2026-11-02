# EGM for Pi

This directory is the Pi package for the Elephant-Goldfish Model (EGM). It
ships the seven EGM skills, the nine canonical reviewer personas, the five
document standards, and the Pi agent definitions that keep the reviewers
read-only.

[Pi](https://pi.dev) is a terminal coding agent that loads skills, prompt
templates, extensions, and themes from a package. Pi substitutes no
plugin-root variable, so this package carries its own copies of the shared
bundle and is installed from the checkout.

## Install

```sh
pi install /absolute/path/to/elephant-goldfish-model/distributions/pi
pi list
```

Invoke a skill as `/skill:egm-brainstorm`, `/skill:egm-draft`, or
`/skill:egm-review`. The skills keep `disable-model-invocation: true`, so Pi
does not offer them for automatic selection.

A Goldfish review needs a fresh-context subagent tool, and Pi itself has none.
A Pi subagent extension supplies one; the tested path is the third-party Gentle
Agents extension in `gentle-pi`, whose `subagent_*` tools read agent definitions
from `~/.pi/agent/agents/`. When no subagent tool is present, the review skills
stop instead of reviewing in the parent context.

```sh
mkdir -p ~/.pi/agent/agents
ln -s /absolute/path/to/elephant-goldfish-model/distributions/pi/subagents/*.md \
  ~/.pi/agent/agents/
```

## Layout

| Path | Contents |
| --- | --- |
| `skills/` | The seven EGM skills, each with its `references/` files |
| `agents/` | The nine canonical personas that every definition reads |
| `subagents/` | The nine Pi agent definitions that set reviewer tools and context rules |
| `resources/` | Execution instructions and the five document standards |
| `docs/` | The runtime guides that the skills and this README link to |
| `PORTING-NOTES.md` | Why the package looks this way, its limits, and the open evidence |

The copies of `skills/`, `agents/`, `resources/`, and `docs/` are regenerated
from the repository root with
`python3 scripts/check_pi_distribution.py --write`. Do not edit them here.

The package omits the OpenAI skill metadata (`skills/*/agents/openai.yaml`), the
development fixtures (`skills/*/test_scenarios.yaml`, `skills/*/TEST.md`), and
the skill and documentation artwork (`skills/*/assets/`, `docs/assets/`)
deliberately: Pi loads none of them, and this README references no artwork.

## Limitations

Pi is not a supported EGM harness yet. No native installation, reviewer
isolation, or end-to-end workflow run is recorded. See the Pi section of the
[harness guide](docs/harnesses.md#pi) for install steps, the tool mapping, and
the known limits, and `PORTING-NOTES.md` for the evidence gaps.

## License

[Apache 2.0](LICENSE). This is not an officially supported Google product.
