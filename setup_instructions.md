# Setup Instructions

## Initialize Git Repository

```bash
cd rawtherapee-composite-generator
git init
git add .
git commit -m "Initial commit: RawTherapee Composite Generator"
```

## Push to GitHub

1. Create a new repository on GitHub named `rawtherapee-composite-generator`
2. Add remote and push:

```bash
git remote add origin https://github.com/yourusername/rawtherapee-composite-generator.git
git branch -M main
git push -u origin main
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Script

```bash
python create_composite.py
```
