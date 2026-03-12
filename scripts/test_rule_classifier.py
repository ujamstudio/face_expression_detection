"""
규칙 기반 감정 분류기 테스트 스크립트

이 스크립트는 ARKit BlendShapes 기반 규칙 분류기를 테스트합니다.

사용법:
    python scripts/test_rule_classifier.py --input data/test_samples/test_mesh.json
    python scripts/test_rule_classifier.py --interactive
"""

import sys
from pathlib import Path
import argparse
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from models.rule_based_classifier import RuleBasedEmotionClassifier
from models.facial_feature_detector import FacialFeatureDetector


def test_single_file(json_path: str):
    """
    단일 JSON 파일 테스트

    Args:
        json_path: 얼굴 메쉬 JSON 파일 경로
    """
    print("="*70)
    print("규칙 기반 감정 분류기 테스트")
    print("="*70)

    # 분류기 초기화
    classifier = RuleBasedEmotionClassifier()

    # 파일 로드
    print(f"\n파일 로드: {json_path}")
    with open(json_path, 'r') as f:
        face_data = json.load(f)

    # 분류
    print("\n감정 분석 중...")
    result = classifier.classify(face_data)

    # 결과 출력
    print("\n" + "="*70)
    print("분석 결과")
    print("="*70)

    print(f"\n✨ 예측 감정: {result['emotion'].upper()}")
    print(f"📊 신뢰도: {result['confidence']:.2%}")
    print(f"📈 점수: {result['score']:.1f}/100")

    print("\n모든 감정 점수:")
    sorted_emotions = sorted(
        result['all_scores'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    for emotion, score in sorted_emotions:
        bar_length = int(score / 2)  # 50점 = 25칸
        bar = "█" * bar_length
        marker = "◀" if emotion == result['emotion'] else ""
        print(f"  {emotion:12s} {score:5.1f} │{bar:25s}│ {marker}")

    # BlendShapes 상세 (상위 10개)
    if 'blendshapes' in result and result['blendshapes']:
        print("\n주요 BlendShapes:")
        sorted_bs = sorted(
            result['blendshapes'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        for key, value in sorted_bs:
            if value > 0.1:  # 0.1 이상만 표시
                bar_length = int(value * 20)
                bar = "▓" * bar_length
                print(f"  {key:25s} {value:.2f} │{bar:20s}│")


def test_interactive():
    """
    대화형 테스트 모드

    사용자가 BlendShapes 값을 직접 입력하여 테스트
    """
    print("="*70)
    print("대화형 감정 테스트")
    print("="*70)
    print("\n7가지 기본 감정을 시뮬레이션합니다.\n")

    classifier = RuleBasedEmotionClassifier()

    # 미리 정의된 테스트 케이스들
    test_cases = {
        '1': {
            'name': '슬픔 (Sadness)',
            'data': {
                'blendshapes': {
                    'jawOpen': 0.3,
                    'mouthFrownLeft': 0.5,
                    'mouthFrownRight': 0.5,
                    'cheekSquintLeft': 0.4,
                    'cheekSquintRight': 0.4,
                    'eyeLookDownLeft': 0.5,
                    'eyeLookDownRight': 0.5,
                    'eyeBlinkLeft': 0.4,
                    'eyeBlinkRight': 0.4,
                }
            }
        },
        '2': {
            'name': '기쁨 (Joy)',
            'data': {
                'blendshapes': {
                    'mouthSmileLeft': 0.8,
                    'mouthSmileRight': 0.8,
                    'cheekSquintLeft': 0.5,
                    'cheekSquintRight': 0.5,
                    'eyeWideLeft': 0.2,
                    'eyeWideRight': 0.2,
                }
            }
        },
        '3': {
            'name': '분노 (Anger)',
            'data': {
                'blendshapes': {
                    'browDownLeft': 0.6,
                    'browDownRight': 0.6,
                    'mouthFrownLeft': 0.4,
                    'mouthFrownRight': 0.4,
                    'mouthPucker': 0.5,
                    'noseSneerLeft': 0.3,
                    'noseSneerRight': 0.3,
                }
            }
        },
        '4': {
            'name': '공포 (Fear)',
            'data': {
                'blendshapes': {
                    'eyeWideLeft': 0.7,
                    'eyeWideRight': 0.7,
                    'browInnerUp': 0.6,
                    'browOuterUpLeft': 0.5,
                    'browOuterUpRight': 0.5,
                    'jawOpen': 0.4,
                }
            }
        },
        '5': {
            'name': '혐오 (Disgust)',
            'data': {
                'blendshapes': {
                    'noseSneerLeft': 0.6,
                    'noseSneerRight': 0.6,
                    'mouthUpperUpLeft': 0.4,
                    'mouthUpperUpRight': 0.4,
                    'mouthFrownLeft': 0.3,
                    'mouthFrownRight': 0.3,
                }
            }
        },
        '6': {
            'name': '놀람 (Surprise)',
            'data': {
                'blendshapes': {
                    'jawOpen': 0.7,
                    'eyeWideLeft': 0.6,
                    'eyeWideRight': 0.6,
                    'browInnerUp': 0.5,
                    'browOuterUpLeft': 0.5,
                    'browOuterUpRight': 0.5,
                }
            }
        },
        '7': {
            'name': '중립 (Neutral)',
            'data': {
                'blendshapes': {
                    'jawOpen': 0.05,
                    'mouthSmileLeft': 0.03,
                    'mouthSmileRight': 0.03,
                }
            }
        }
    }

    while True:
        print("\n테스트할 표정을 선택하세요:")
        for key, case in test_cases.items():
            print(f"  {key}. {case['name']}")
        print("  0. 종료")

        choice = input("\n선택: ").strip()

        if choice == '0':
            print("\n테스트를 종료합니다.")
            break

        if choice not in test_cases:
            print("⚠️  잘못된 선택입니다.")
            continue

        # 선택한 케이스 테스트
        case = test_cases[choice]
        print(f"\n{'='*70}")
        print(f"테스트: {case['name']}")
        print(f"{'='*70}")

        result = classifier.classify(case['data'])

        # 결과 출력
        correct = result['emotion'] in case['name'].lower()
        status = "✅ 정확!" if correct else "❌ 오류"

        print(f"\n{status}")
        print(f"예측: {result['emotion'].upper()}")
        print(f"신뢰도: {result['confidence']:.2%}")
        print(f"점수: {result['score']:.1f}")

        print("\n상위 3개 감정:")
        sorted_emotions = sorted(
            result['all_scores'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        for i, (emotion, score) in enumerate(sorted_emotions, 1):
            print(f"  {i}. {emotion:12s}: {score:5.1f}")

        input("\n계속하려면 Enter를 누르세요...")


def test_batch(input_dir: str):
    """
    디렉토리 내 모든 JSON 파일 일괄 테스트

    Args:
        input_dir: JSON 파일들이 있는 디렉토리
    """
    print("="*70)
    print("배치 테스트 모드")
    print("="*70)

    classifier = RuleBasedEmotionClassifier()
    input_path = Path(input_dir)

    # JSON 파일 찾기
    json_files = list(input_path.rglob('*.json'))

    if not json_files:
        print(f"\n⚠️  {input_dir}에서 JSON 파일을 찾을 수 없습니다.")
        return

    print(f"\n{len(json_files)}개 파일을 찾았습니다.\n")

    results = []

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                face_data = json.load(f)

            result = classifier.classify(face_data)
            results.append({
                'file': json_file.name,
                'emotion': result['emotion'],
                'confidence': result['confidence'],
                'score': result['score']
            })

            print(f"✓ {json_file.name:30s} → {result['emotion']:10s} "
                  f"({result['confidence']:.1%})")

        except Exception as e:
            print(f"✗ {json_file.name:30s} → 오류: {e}")

    # 요약
    print("\n" + "="*70)
    print("요약")
    print("="*70)

    from collections import Counter
    emotion_counts = Counter(r['emotion'] for r in results)

    print("\n감정 분포:")
    for emotion, count in emotion_counts.most_common():
        print(f"  {emotion:12s}: {count:3d}개")

    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    print(f"\n평균 신뢰도: {avg_confidence:.2%}")


def main():
    parser = argparse.ArgumentParser(
        description='규칙 기반 감정 분류기 테스트'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='테스트할 JSON 파일 경로'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='대화형 테스트 모드'
    )
    parser.add_argument(
        '--batch',
        type=str,
        help='배치 테스트할 디렉토리'
    )

    args = parser.parse_args()

    if args.interactive:
        test_interactive()
    elif args.input:
        test_single_file(args.input)
    elif args.batch:
        test_batch(args.batch)
    else:
        # 기본: 대화형 모드
        test_interactive()


if __name__ == "__main__":
    main()
