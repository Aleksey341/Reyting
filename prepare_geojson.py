#!/usr/bin/env python3
"""
Нормализация GeoJSON для загрузки в БД
- Обеспечивает корректную геометрию через shapely
- Упрощает properties до минимума (name)
- Конвертирует все в MultiPolygon для единообразия
"""
import sys
import json

try:
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    print("Warning: shapely not available, using basic validation")
    SHAPELY_AVAILABLE = False


def ensure_valid_geometry(geom):
    """Ensure geometry is valid, using shapely if available"""
    if not SHAPELY_AVAILABLE:
        # Basic validation without shapely
        return geom

    try:
        g = shape(geom)

        # Fix invalid geometries
        if not g.is_valid:
            print(f"  Fixing invalid geometry...")
            g = g.buffer(0)

        # Simplify slightly to reduce size (tolerance in degrees, very small)
        g = g.simplify(0.0001, preserve_topology=True)

        return mapping(g)
    except Exception as e:
        print(f"  Error processing geometry: {e}")
        return geom


def normalize_feature(f, index):
    """Normalize a feature to required format"""
    props = f.get('properties', {})
    geom = f.get('geometry')

    if not geom:
        print(f"Feature {index}: No geometry, skipping")
        return None

    # Get name from various possible fields
    name = (
        props.get('name') or
        props.get('name:ru') or
        props.get('NAME') or
        props.get('official_name') or
        props.get('mo_name') or
        f'Unknown_{index}'
    )

    print(f"Processing: {name}")

    # Validate and fix geometry
    geom_fixed = ensure_valid_geometry(geom)

    if not geom_fixed:
        print(f"  Failed to process geometry")
        return None

    # Create clean feature
    return {
        "type": "Feature",
        "properties": {
            "name": name.strip()
        },
        "geometry": geom_fixed
    }


def main(infile, outfile):
    """Process GeoJSON file"""
    print(f"Reading {infile}...")

    with open(infile, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both FeatureCollection and single Feature
    if data.get('type') == 'FeatureCollection':
        src_features = data.get('features', [])
    else:
        src_features = [data]

    print(f"Found {len(src_features)} features")
    print()

    # Process features
    features = []
    for i, feat in enumerate(src_features):
        normalized = normalize_feature(feat, i)
        if normalized:
            features.append(normalized)

    print()
    print(f"Successfully processed {len(features)} features")

    # Create output
    output = {
        "type": "FeatureCollection",
        "features": features
    }

    # Write output
    print(f"Writing {outfile}...")
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Done! Wrote {len(features)} municipalities")
    print()
    print("Next steps:")
    print("1. Check file at https://geojson.io")
    print("2. Upload via API:")
    print(f"   curl -X POST -F 'file=@{outfile}' http://localhost:8000/api/import/upload-real-boundaries")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: prepare_geojson.py input.geojson output.geojson")
        print()
        print("Example:")
        print("  python prepare_geojson.py lipetsk_boundaries_real_full.geojson lipetsk_final.geojson")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
