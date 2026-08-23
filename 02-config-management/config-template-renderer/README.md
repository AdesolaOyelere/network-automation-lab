# Config Template Renderer

> Renders deterministic IOS-style device configurations from reusable templates
> and structured JSON data, with strict validation and no external dependencies.

**Category:** `02-config-management` · **Skills:** configuration templating, structured data, validation, Python

## Problem

Copying device configurations by hand makes repeated patterns difficult to maintain
and lets missing values reach deployment unnoticed. Network engineers need a way to
separate reusable configuration structure from per-device facts and fail early when
either one is incomplete.

## Approach

`template_renderer.py` implements a deliberately small template language. Scalar
tags such as `{{hostname}}` and dotted lookups such as `{{ipv4.address}}` insert
values, while `{{#interfaces}}...{{/interfaces}}` sections repeat for lists of
objects. Sections may nest, and inner records can still use values from a parent
scope.

The renderer parses templates into a syntax tree before producing output. It rejects
missing values, unmatched section tags, non-scalar substitutions, and incorrectly
shaped section data instead of emitting a partial configuration. The focused syntax
does not evaluate expressions or execute code.

`device_data.json` and `ios_config.template` are synthetic committed inputs. The
project only renders text; it never connects to or changes a real network device.

## How to run

```bash
python3 -m pytest
python3 run.py
```

The runner accepts `--template`, `--data`, and `--output` overrides and writes a
reproducible rendered configuration plus a JSON summary under `results/`.

## Sample output

The committed inputs render a 22-line, 489-byte configuration. An excerpt is:

```text
hostname branch-rtr-02
ip name-server 192.0.2.53
ip name-server 192.0.2.54
interface GigabitEthernet0/1
 description User LAN
 ip address 10.40.0.1 255.255.255.0
 ip helper-address 10.99.0.10
 ip helper-address 10.99.0.11
 no shutdown
```

The complete executed output is in `results/rendered_config.txt`.

## What this demonstrates

- Parsing and recursively evaluating a constrained configuration template language.
- Separating reusable configuration intent from structured per-device data.
- Strict error handling and end-to-end regression checks against generated artifacts.
