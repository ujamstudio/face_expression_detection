#!/usr/bin/env python3
"""
Validate BlendShapes in exported JSON files from iOS app

This script checks:
1. JSON structure is correct
2. BlendShapes are present and valid
3. Data can be used with rule-based classifier

Usage:
    python scripts/validate_blendshapes.py --file exported_mesh.json
    python scripts/validate_blendshapes.py --dir /path/to/exports/
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

# Expected BlendShape keys (52 total from ARKit)
EXPECTED_BLENDSHAPES = [
    # Eyes
    'eyeBlinkLeft', 'eyeBlinkRight',
    'eyeLookDownLeft', 'eyeLookDownRight',
    'eyeLookInLeft', 'eyeLookInRight',
    'eyeLookOutLeft', 'eyeLookOutRight',
    'eyeLookUpLeft', 'eyeLookUpRight',
    'eyeSquintLeft', 'eyeSquintRight',
    'eyeWideLeft', 'eyeWideRight',

    # Jaw
    'jawForward', 'jawLeft', 'jawRight', 'jawOpen',

    # Mouth
    'mouthClose', 'mouthFunnel', 'mouthPucker',
    'mouthLeft', 'mouthRight',
    'mouthSmileLeft', 'mouthSmileRight',
    'mouthFrownLeft', 'mouthFrownRight',
    'mouthDimpleLeft', 'mouthDimpleRight',
    'mouthStretchLeft', 'mouthStretchRight',
    'mouthRollLower', 'mouthRollUpper',
    'mouthShrugLower', 'mouthShrugUpper',
    'mouthPressLeft', 'mouthPressRight',
    'mouthLowerDownLeft', 'mouthLowerDownRight',
    'mouthUpperUpLeft', 'mouthUpperUpRight',

    # Eyebrows
    'browDownLeft', 'browDownRight',
    'browInnerUp',
    'browOuterUpLeft', 'browOuterUpRight',

    # Cheeks
    'cheekPuff',
    'cheekSquintLeft', 'cheekSquintRight',

    # Nose
    'noseSneerLeft', 'noseSneerRight',

    # Tongue
    'tongueOut'
]


def validate_json_structure(data: Dict[str, Any]) -> List[str]:
    """Validate the basic JSON structure"""
    errors = []
    warnings = []

    # Check required fields
    required_fields = ['vertices', 'emotion', 'timestamp']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check vertices
    if 'vertices' in data:
        if not isinstance(data['vertices'], list):
            errors.append("'vertices' must be a list")
        elif len(data['vertices']) == 0:
            errors.append("'vertices' is empty")
        elif not all(isinstance(v, list) and len(v) > 0 for v in data['vertices']):
            errors.append("'vertices' contains invalid vertex data")

    # Check BlendShapes
    if 'blendshapes' not in data:
        warnings.append("'blendshapes' field not found (old format?)")
    else:
        if not isinstance(data['blendshapes'], list):
            errors.append("'blendshapes' must be a list")
        elif len(data['blendshapes']) == 0:
            warnings.append("'blendshapes' is empty")

    return errors, warnings


def validate_blendshapes(data: Dict[str, Any]) -> List[str]:
    """Validate BlendShapes data"""
    errors = []
    warnings = []

    if 'blendshapes' not in data:
        return errors, warnings

    blendshapes = data['blendshapes']

    # Check frame count matches
    if 'vertices' in data:
        vertex_count = len(data['vertices'])
        blendshape_count = len(blendshapes)

        if vertex_count != blendshape_count:
            errors.append(f"Frame count mismatch: {vertex_count} vertices vs {blendshape_count} blendshapes")

    # Validate each frame's BlendShapes
    for i, frame_blendshapes in enumerate(blendshapes):
        if not isinstance(frame_blendshapes, dict):
            errors.append(f"Frame {i}: BlendShapes must be a dictionary")
            continue

        # Check for expected keys
        missing_keys = set(EXPECTED_BLENDSHAPES) - set(frame_blendshapes.keys())
        extra_keys = set(frame_blendshapes.keys()) - set(EXPECTED_BLENDSHAPES)

        if i == 0:  # Only report for first frame to avoid spam
            if missing_keys:
                warnings.append(f"Missing BlendShape keys: {', '.join(sorted(missing_keys))}")
            if extra_keys:
                warnings.append(f"Unexpected BlendShape keys: {', '.join(sorted(extra_keys))}")

        # Validate values
        for key, value in frame_blendshapes.items():
            if not isinstance(value, (int, float)):
                errors.append(f"Frame {i}, {key}: Value must be numeric, got {type(value)}")
            elif not 0 <= value <= 1:
                warnings.append(f"Frame {i}, {key}: Value {value} outside [0, 1] range")

    return errors, warnings


def analyze_blendshapes(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze BlendShapes statistics"""
    if 'blendshapes' not in data or not data['blendshapes']:
        return {}

    blendshapes = data['blendshapes']
    stats = {
        'frame_count': len(blendshapes),
        'parameters_per_frame': len(blendshapes[0]) if blendshapes else 0,
        'active_features': {},
        'max_values': {},
        'avg_values': {}
    }

    # Calculate statistics
    all_keys = set()
    for frame in blendshapes:
        all_keys.update(frame.keys())

    for key in all_keys:
        values = [frame.get(key, 0) for frame in blendshapes]
        if values:
            max_val = max(values)
            avg_val = sum(values) / len(values)

            stats['max_values'][key] = round(max_val, 3)
            stats['avg_values'][key] = round(avg_val, 3)

            # Consider feature active if max > 0.1
            if max_val > 0.1:
                stats['active_features'][key] = max_val

    return stats


def test_with_classifier(data: Dict[str, Any]) -> Dict[str, Any]:
    """Test data with rule-based classifier"""
    try:
        # Add src to path
        sys.path.append(str(Path(__file__).parent.parent / 'src'))
        from models.rule_based_classifier import RuleBasedEmotionClassifier

        classifier = RuleBasedEmotionClassifier()

        # Test with first frame if multi-frame, or whole data if single
        if 'blendshapes' in data and isinstance(data['blendshapes'], list) and data['blendshapes']:
            # Multi-frame: test first frame
            test_data = {
                'blendshapes': data['blendshapes'][0]
            }
        else:
            test_data = data

        result = classifier.classify(test_data)
        return {
            'success': True,
            'emotion': result['emotion'],
            'confidence': result['confidence'],
            'score': result['score']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def validate_file(filepath: Path) -> None:
    """Validate a single JSON file"""
    print(f"\n{'='*70}")
    print(f"Validating: {filepath.name}")
    print(f"{'='*70}")

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Structure validation
    errors, warnings = validate_json_structure(data)

    # BlendShapes validation
    bs_errors, bs_warnings = validate_blendshapes(data)
    errors.extend(bs_errors)
    warnings.extend(bs_warnings)

    # Print results
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")

    if not errors:
        print("\n✅ Structure validation PASSED")

    # Analyze BlendShapes
    stats = analyze_blendshapes(data)
    if stats:
        print("\n📊 BLENDSHAPES ANALYSIS:")
        print(f"  • Frames: {stats['frame_count']}")
        print(f"  • Parameters per frame: {stats['parameters_per_frame']}")
        print(f"  • Active features: {len(stats['active_features'])}")

        if stats['active_features']:
            print("\n  Top active features:")
            sorted_features = sorted(stats['active_features'].items(), key=lambda x: x[1], reverse=True)[:5]
            for key, value in sorted_features:
                print(f"    - {key:25s}: {value:.3f}")

    # Test with classifier
    if 'blendshapes' in data:
        print("\n🤖 CLASSIFIER TEST:")
        result = test_with_classifier(data)

        if result['success']:
            expected = data.get('emotion', 'unknown')
            predicted = result['emotion']
            match = "✅" if expected.lower() == predicted.lower() else "❌"

            print(f"  • Expected: {expected}")
            print(f"  • Predicted: {predicted} {match}")
            print(f"  • Confidence: {result['confidence']:.2%}")
            print(f"  • Score: {result['score']:.1f}/100")
        else:
            print(f"  ❌ Classifier error: {result['error']}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate BlendShapes in exported JSON files'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--file',
        type=str,
        help='Single JSON file to validate'
    )
    group.add_argument(
        '--dir',
        type=str,
        help='Directory containing JSON files'
    )

    args = parser.parse_args()

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            sys.exit(1)
        validate_file(filepath)

    elif args.dir:
        dirpath = Path(args.dir)
        if not dirpath.exists():
            print(f"❌ Directory not found: {dirpath}")
            sys.exit(1)

        json_files = list(dirpath.glob('*.json'))
        if not json_files:
            print(f"❌ No JSON files found in {dirpath}")
            sys.exit(1)

        print(f"Found {len(json_files)} JSON files")

        for filepath in json_files:
            validate_file(filepath)

        print(f"\n{'='*70}")
        print(f"Validated {len(json_files)} files")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()