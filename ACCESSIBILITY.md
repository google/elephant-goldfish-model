# Accessibility

We want people with disabilities to be able to use and contribute to the
Elephant-Goldfish Model (EGM). Accessibility reports and contributions are
welcome.

## Scope and goals

This statement covers the repository's documentation, shared skill content,
and the [EGM website](https://egm.dev).

Our goal for the website is the Web Content Accessibility Guidelines
[WCAG 2.2 Level AA](https://www.w3.org/TR/WCAG22/).
This is a target, not a claim of verified conformance.

Priorities include keyboard access, visible focus, readable text, sufficient
contrast, clear headings and links, text alternatives, and reduced motion.
For documentation and generated reports, prefer plain language and text that
does not depend on color or a diagram alone to convey meaning.

## Environments and current limits

EGM provides Markdown skills and documentation. Its interactive experience
runs inside a coding agent or host application. See the
[harness guide](docs/harnesses.md) for installation and verification limits.
Host support does not establish accessibility support.

The website includes a skip link, keyboard focus styles, and reduced-motion
styles. These features do not establish that every page is accessible.
This statement does not certify any browser, screen reader, terminal, or
host application combination. A comprehensive accessibility audit and
assistive-technology test matrix have not been established for this statement.

Known limits include:

- Host applications control their own chat, terminal, and plugin interfaces.
  EGM cannot correct every barrier in those interfaces.
- Model-generated documents may contain unclear text, complex tables, or
  diagrams without adequate text explanations. Human review is still needed.
- Automated unit and build checks do not establish keyboard usability,
  screen reader support, or WCAG conformance.

The source documentation can be read as Markdown when a rendered view is
difficult to use. You can also ask your coding agent for a plain-text report
or a text explanation of a diagram. These options may help, but do not
replace fixing the underlying barrier.

## Report an accessibility barrier

Use the [bug report template](https://github.com/google/elephant-goldfish-model/issues/new?template=bug_report.md)
and identify the report as an accessibility issue. Include what you can:

- The page, document, skill, or task affected.
- What you expected and what prevented you from completing the task.
- Steps to reproduce, including keyboard actions when relevant.
- Browser or host, operating system, and assistive technology versions.
- Whether a workaround exists and whether the barrier blocks a core task.

Screenshots and recordings are optional. Do not include credentials, private
project content, or medical information. Reports do not need to name a WCAG
criterion or include a proposed fix.

## Contribute accessibility improvements

Follow the [contributing guide](CONTRIBUTING.md). Describe the barrier and
record the checks performed. For website changes, check keyboard navigation,
focus visibility, zoom and reflow, and affected screen reader behavior when
possible. State any checks that could not be performed. Use automated checks
alongside manual testing, and provide text alternatives for meaningful images
and diagrams.
