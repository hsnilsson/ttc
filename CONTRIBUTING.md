# Contributing to Test Target Cropper (ttc)

First of all: **thank you**. This is a small, one‑person project and any help is welcome—bug reports, ideas, docs, code, all of it.

## Ways you can help

- **Report bugs**: open a GitHub issue with:
  - what you ran (command, sample files if possible)
  - what you expected
  - what actually happened (including error text and platform)

- **Suggest improvements**: open an issue for feature ideas or UX tweaks. Rough ideas are fine; we can discuss details there.

- **Send pull requests**:
  - Small, focused PRs are ideal.
  - Draft PRs are totally welcome if you just want early feedback.

## Quick dev setup

```bash
git clone https://github.com/hsnilsson/ttc.git
cd ttc
pip install -r requirements.txt
python ttc.py --help
```

If you can, test your change on at least one real image set before opening a PR.

## Style & expectations

There are no heavy rules here:

- Try to keep the code readable and roughly PEP 8‑ish.
- Prefer clear names over cleverness.
- If you touch behavior, a short note in `CHANGELOG.md` or `README.md` is appreciated.

Don’t worry about being perfect—if something needs tweaking, we can adjust it in review.

## License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the rest of the project).
