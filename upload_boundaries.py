#!/usr/bin/env python3
"""
Скрипт для загрузки реальных границ в БД через API
"""
import requests
import sys
import json


def upload_boundaries(api_url, geojson_file):
    """Upload GeoJSON file to API"""
    print(f"Uploading {geojson_file} to {api_url}...")
    print()

    # Prepare file for upload
    with open(geojson_file, 'rb') as f:
        files = {'file': (geojson_file, f, 'application/geo+json')}

        try:
            # Send POST request
            response = requests.post(
                f"{api_url}/api/import/upload-real-boundaries",
                files=files,
                timeout=60
            )

            # Check response
            response.raise_for_status()
            result = response.json()

            # Display results
            print("✓ SUCCESS!")
            print()
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            print(f"Updated: {result.get('updated')} municipalities")

            if result.get('not_found'):
                print()
                print(f"Not found in DB: {result.get('not_found')}")

            if result.get('errors'):
                print()
                print("Errors:")
                for err in result.get('errors', []):
                    print(f"  - {err}")

            print()
            print("✓ Boundaries successfully uploaded to database!")
            print()
            print("Next steps:")
            print("1. Open dashboard: {}/map".format(api_url.replace('/api', '')))
            print("2. Check that municipalities now show real boundaries")

            return True

        except requests.exceptions.RequestException as e:
            print(f"✗ ERROR: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_boundaries.py <geojson_file> [api_url]")
        print()
        print("Examples:")
        print("  # Local development:")
        print("  python upload_boundaries.py lipetsk_municipalities_clean.geojson")
        print()
        print("  # Production (Amvera):")
        print("  python upload_boundaries.py lipetsk_municipalities_clean.geojson https://your-app.amvera.io")
        sys.exit(1)

    geojson_file = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"

    # Remove trailing slash
    api_url = api_url.rstrip('/')

    # Check file exists
    try:
        with open(geojson_file, 'r') as f:
            data = json.load(f)
            feature_count = len(data.get('features', []))
            print(f"File: {geojson_file}")
            print(f"Features: {feature_count}")
            print(f"API URL: {api_url}")
            print()
    except FileNotFoundError:
        print(f"✗ ERROR: File not found: {geojson_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ ERROR: Invalid JSON in {geojson_file}")
        sys.exit(1)

    # Upload
    success = upload_boundaries(api_url, geojson_file)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
