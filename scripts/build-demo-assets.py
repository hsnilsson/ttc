"""Build public, lossless example crops from an explicitly selected TTC job.

The DNG originals, native logs, job IDs and real scores are never published.
Use --reference-preview to verify a freshly rendered source against the job.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


def build(source_dir, job_dir, destination, reference_preview):
    raw = json.loads((job_dir / 'manifest.json').read_text(encoding='utf-8'))
    if destination.exists():
        raise ValueError('Use a fresh destination; existing demo assets are not overwritten')
    preview = job_dir / 'run-1/reference.png'
    with Image.open(reference_preview) as fresh, Image.open(preview) as saved:
        if fresh.size != saved.size or ImageChops.difference(fresh.convert('RGB'), saved.convert('RGB')).getbbox():
            raise ValueError('The source reference preview does not match this TTC job')
    native_log = (job_dir / 'native.log').read_text(encoding='utf-8')
    for frame in raw['frames']:
        source = source_dir / frame['label']
        if not source.is_file() or str(source) not in native_log:
            raise ValueError(f"Job does not establish the requested source: {frame['label']}")
        if len(frame['regions']) != 5:
            raise ValueError('Each example capture must have five real crops')
    assets = destination / 'assets'
    assets.mkdir(parents=True)
    with Image.open(preview) as image:
        image.convert('RGB').save(assets / 'target.webp', lossless=True, method=6)
    sample = {
        'schema_version': 1, 'width': raw['width'], 'height': raw['height'],
        'preview': {'url': 'assets/target.webp', 'width': raw['width'], 'height': raw['height']},
        'rois': raw['rois'], 'tracking_radius': raw.get('tracking_radius', 16),
        'warnings': ['DEMO — timings, detection and sharpness scores are simulated. '
                     'Images are example captures, not measurements of your setup.'],
        'captures': [], 'apertures': [],
    }
    apertures = sorted({f['aperture'] for f in raw['frames']})
    for index, frame in enumerate(raw['frames']):
        group = apertures.index(frame['aperture'])
        repeat = sum(c['aperture'] == frame['aperture'] for c in sample['captures']) + 1
        capture = {'id': f'demo-{index+1:02}', 'name': frame['label'], 'aperture': frame['aperture'],
                   'apertureSource': 'example metadata', 'repeat': repeat, 'flags': [], 'measurements': {}}
        for region_index, region in enumerate(frame['regions']):
            source = job_dir / 'run-1' / Path(region['crop_url']).name
            name = f'capture-{index+1:02}-{region["id"]}.webp'
            with Image.open(source) as image:
                if image.size != (region['width'], region['height']):
                    raise ValueError(f'Crop dimensions differ: {source.name}')
                image.convert('RGB').save(assets / name, lossless=True, method=6)
            # Deliberate illustrative scores, unrelated to native measurements.
            peak = 1 if region['id'] == 'center' else 3
            value = round(max(.04, .22 - abs(group-peak)*.016 - region_index*.008 + (repeat-1)*.002), 4)
            capture['measurements'][region['id']] = {
                'value': value, 'uncertainty': .001, 'status': 'accepted',
                'flags': [], 'crop': {'url': 'assets/' + name, 'width': region['width'], 'height': region['height']},
            }
        sample['captures'].append(capture)
    for aperture in apertures:
        sample['apertures'].append({'value': aperture, 'selectedCaptureId': next(c['id'] for c in sample['captures'] if c['aperture'] == aperture), 'flags': []})
    (destination / 'sample.json').write_text(json.dumps(sample, indent=2) + '\n', encoding='utf-8')
    print(f"Built {len(sample['captures'])} example captures; {sum(p.stat().st_size for p in assets.iterdir()):,} asset bytes")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-dir', 'job-dir', 'destination', 'reference-preview'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.source_dir, args.job_dir, args.destination, args.reference_preview)
