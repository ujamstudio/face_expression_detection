"""
Facial Feature Detector using ARKit BlendShapes

이 모듈은 ARKit BlendShapes와 3D 얼굴 메쉬를 분석하여
표정의 물리적 특징을 추출합니다.

슬픔 표정 특징:
1. 입 벌림
2. 입꼬리 내림
3. 뺨 올림
4. 뺨-입꼬리 반대 긴장
5. 시선 아래
6. 눈꺼풀 처짐
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple


class FacialFeatureDetector:
    """
    ARKit BlendShapes 기반 표정 특징 감지기
    """

    # ARKit BlendShapes 키 (52개 중 주요 것들)
    BLENDSHAPE_KEYS = {
        # 눈 (Eyes)
        'eyeBlinkLeft': 'eyeBlinkLeft',
        'eyeBlinkRight': 'eyeBlinkRight',
        'eyeWideLeft': 'eyeWideLeft',
        'eyeWideRight': 'eyeWideRight',
        'eyeLookUpLeft': 'eyeLookUpLeft',
        'eyeLookUpRight': 'eyeLookUpRight',
        'eyeLookDownLeft': 'eyeLookDownLeft',
        'eyeLookDownRight': 'eyeLookDownRight',

        # 눈썹 (Eyebrows)
        'browDownLeft': 'browDownLeft',
        'browDownRight': 'browDownRight',
        'browInnerUp': 'browInnerUp',
        'browOuterUpLeft': 'browOuterUpLeft',
        'browOuterUpRight': 'browOuterUpRight',

        # 입 (Mouth)
        'jawOpen': 'jawOpen',
        'mouthFrownLeft': 'mouthFrownLeft',
        'mouthFrownRight': 'mouthFrownRight',
        'mouthSmileLeft': 'mouthSmileLeft',
        'mouthSmileRight': 'mouthSmileRight',
        'mouthPucker': 'mouthPucker',
        'mouthFunnel': 'mouthFunnel',
        'mouthLeft': 'mouthLeft',
        'mouthRight': 'mouthRight',
        'mouthUpperUpLeft': 'mouthUpperUpLeft',
        'mouthUpperUpRight': 'mouthUpperUpRight',
        'mouthLowerDownLeft': 'mouthLowerDownLeft',
        'mouthLowerDownRight': 'mouthLowerDownRight',

        # 뺨 (Cheeks)
        'cheekSquintLeft': 'cheekSquintLeft',
        'cheekSquintRight': 'cheekSquintRight',
        'cheekPuff': 'cheekPuff',

        # 코 (Nose)
        'noseSneerLeft': 'noseSneerLeft',
        'noseSneerRight': 'noseSneerRight',
    }

    def __init__(self):
        """Initialize the facial feature detector."""
        pass

    def load_face_data(self, json_path: str) -> Dict:
        """
        얼굴 메쉬 JSON 파일 로드

        Args:
            json_path: JSON 파일 경로

        Returns:
            얼굴 데이터 딕셔너리
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data

    def extract_blendshapes(self, face_data: Dict) -> Dict[str, float]:
        """
        BlendShapes 추출

        Args:
            face_data: 얼굴 데이터 딕셔너리

        Returns:
            BlendShape 값들 (0.0 ~ 1.0)
        """
        blendshapes = face_data.get('blendshapes', {})

        # BlendShapes가 없으면 빈 딕셔너리 반환
        if not blendshapes:
            print("Warning: No blendshapes found in data")
            return {}

        return blendshapes

    def extract_vertices(self, face_data: Dict) -> np.ndarray:
        """
        3D 정점 추출

        Args:
            face_data: 얼굴 데이터 딕셔너리

        Returns:
            정점 배열 (N, 3)
        """
        vertices = np.array(face_data.get('vertices', []), dtype=np.float32)
        return vertices

    # ===== 슬픔 표정 특징 감지 함수들 =====

    def detect_mouth_open(self, blendshapes: Dict) -> Tuple[float, bool]:
        """
        특징 1: 입 벌림 감지

        Returns:
            (측정값, 감지 여부)
        """
        jaw_open = blendshapes.get('jawOpen', 0.0)
        threshold = 0.2
        detected = jaw_open > threshold
        return jaw_open, detected

    def detect_mouth_frown(self, blendshapes: Dict) -> Tuple[float, bool]:
        """
        특징 2: 입꼬리 내림 감지

        Returns:
            (평균 측정값, 감지 여부)
        """
        frown_left = blendshapes.get('mouthFrownLeft', 0.0)
        frown_right = blendshapes.get('mouthFrownRight', 0.0)

        avg_frown = (frown_left + frown_right) / 2.0
        threshold = 0.3
        detected = avg_frown > threshold

        return avg_frown, detected

    def detect_cheek_raise(self, blendshapes: Dict) -> Tuple[float, bool]:
        """
        특징 3: 뺨 올림 감지 (눈을 가늘게 뜨는 동작)

        Returns:
            (평균 측정값, 감지 여부)
        """
        cheek_left = blendshapes.get('cheekSquintLeft', 0.0)
        cheek_right = blendshapes.get('cheekSquintRight', 0.0)

        avg_cheek = (cheek_left + cheek_right) / 2.0
        threshold = 0.2
        detected = avg_cheek > threshold

        return avg_cheek, detected

    def detect_opposing_tension(
        self,
        mouth_frown: float,
        cheek_raise: float
    ) -> Tuple[float, bool]:
        """
        특징 4: 입꼬리 내림 + 뺨 올림 동시 발생 (반대 방향 긴장)

        슬픔의 특징적인 표정: 입은 내리고 뺨은 올라가는 긴장

        Returns:
            (긴장 점수, 감지 여부)
        """
        # 둘 다 활성화되어 있는 정도
        tension_score = min(mouth_frown, cheek_raise)

        # 둘 다 어느 정도 이상 활성화되어야 함
        threshold = 0.15
        detected = (mouth_frown > threshold and cheek_raise > threshold)

        return tension_score, detected

    def detect_gaze_down(self, blendshapes: Dict) -> Tuple[float, bool]:
        """
        특징 5: 시선 아래로 향함

        Returns:
            (평균 측정값, 감지 여부)
        """
        look_down_left = blendshapes.get('eyeLookDownLeft', 0.0)
        look_down_right = blendshapes.get('eyeLookDownRight', 0.0)

        avg_look_down = (look_down_left + look_down_right) / 2.0
        threshold = 0.3
        detected = avg_look_down > threshold

        return avg_look_down, detected

    def detect_eyelid_droop(self, blendshapes: Dict) -> Tuple[float, bool]:
        """
        특징 6: 눈꺼풀 처짐 (반쯤 감긴 눈)

        완전히 감은 것(blink)과 다름 - 약간만 처진 상태

        Returns:
            (처짐 정도, 감지 여부)
        """
        # 눈 깜빡임이 완전하지 않고 부분적인 경우
        blink_left = blendshapes.get('eyeBlinkLeft', 0.0)
        blink_right = blendshapes.get('eyeBlinkRight', 0.0)

        # 0.2~0.6 범위가 처짐 (완전히 감지 않음)
        droop_score = 0.0
        if 0.2 < blink_left < 0.6:
            droop_score += blink_left
        if 0.2 < blink_right < 0.6:
            droop_score += blink_right

        droop_score /= 2.0

        threshold = 0.2
        detected = droop_score > threshold

        return droop_score, detected

    def analyze_sadness_features(self, face_data: Dict) -> Dict:
        """
        슬픔 표정의 모든 특징을 종합 분석

        Args:
            face_data: 얼굴 데이터

        Returns:
            분석 결과 딕셔너리
        """
        blendshapes = self.extract_blendshapes(face_data)

        if not blendshapes:
            return {
                'features': {},
                'total_score': 0.0,
                'detected_features': [],
                'is_sadness': False,
                'confidence': 0.0
            }

        # 각 특징 감지
        mouth_open_val, mouth_open_detected = self.detect_mouth_open(blendshapes)
        mouth_frown_val, mouth_frown_detected = self.detect_mouth_frown(blendshapes)
        cheek_raise_val, cheek_raise_detected = self.detect_cheek_raise(blendshapes)
        tension_val, tension_detected = self.detect_opposing_tension(
            mouth_frown_val, cheek_raise_val
        )
        gaze_down_val, gaze_down_detected = self.detect_gaze_down(blendshapes)
        eyelid_droop_val, eyelid_droop_detected = self.detect_eyelid_droop(blendshapes)

        # 점수 계산 (각 특징의 가중치)
        feature_weights = {
            'mouth_open': 20,
            'mouth_frown': 25,
            'cheek_raise': 20,
            'opposing_tension': 15,
            'gaze_down': 10,
            'eyelid_droop': 10
        }

        total_score = 0.0
        detected_features = []

        if mouth_open_detected:
            total_score += feature_weights['mouth_open']
            detected_features.append('mouth_open')

        if mouth_frown_detected:
            total_score += feature_weights['mouth_frown']
            detected_features.append('mouth_frown')

        if cheek_raise_detected:
            total_score += feature_weights['cheek_raise']
            detected_features.append('cheek_raise')

        if tension_detected:
            total_score += feature_weights['opposing_tension']
            detected_features.append('opposing_tension')

        if gaze_down_detected:
            total_score += feature_weights['gaze_down']
            detected_features.append('gaze_down')

        if eyelid_droop_detected:
            total_score += feature_weights['eyelid_droop']
            detected_features.append('eyelid_droop')

        # 슬픔 판정 (70점 이상)
        sadness_threshold = 70
        is_sadness = total_score >= sadness_threshold
        confidence = min(total_score / 100.0, 1.0)

        return {
            'features': {
                'mouth_open': {
                    'value': float(mouth_open_val),
                    'detected': mouth_open_detected,
                    'score': feature_weights['mouth_open'] if mouth_open_detected else 0
                },
                'mouth_frown': {
                    'value': float(mouth_frown_val),
                    'detected': mouth_frown_detected,
                    'score': feature_weights['mouth_frown'] if mouth_frown_detected else 0
                },
                'cheek_raise': {
                    'value': float(cheek_raise_val),
                    'detected': cheek_raise_detected,
                    'score': feature_weights['cheek_raise'] if cheek_raise_detected else 0
                },
                'opposing_tension': {
                    'value': float(tension_val),
                    'detected': tension_detected,
                    'score': feature_weights['opposing_tension'] if tension_detected else 0
                },
                'gaze_down': {
                    'value': float(gaze_down_val),
                    'detected': gaze_down_detected,
                    'score': feature_weights['gaze_down'] if gaze_down_detected else 0
                },
                'eyelid_droop': {
                    'value': float(eyelid_droop_val),
                    'detected': eyelid_droop_detected,
                    'score': feature_weights['eyelid_droop'] if eyelid_droop_detected else 0
                }
            },
            'total_score': float(total_score),
            'detected_features': detected_features,
            'is_sadness': is_sadness,
            'confidence': float(confidence),
            'threshold': sadness_threshold
        }


if __name__ == "__main__":
    # 테스트 코드
    print("="*70)
    print("슬픔 표정 특징 감지기 테스트")
    print("="*70)

    # 테스트 데이터 생성 (슬픔 표정 시뮬레이션)
    test_data_sadness = {
        'vertices': [[0.1, 0.2, 0.3]] * 100,  # 더미 정점
        'blendshapes': {
            'jawOpen': 0.3,              # 입 벌림
            'mouthFrownLeft': 0.4,       # 입꼬리 내림 (왼쪽)
            'mouthFrownRight': 0.4,      # 입꼬리 내림 (오른쪽)
            'cheekSquintLeft': 0.3,      # 뺨 올림 (왼쪽)
            'cheekSquintRight': 0.3,     # 뺨 올림 (오른쪽)
            'eyeLookDownLeft': 0.4,      # 시선 아래 (왼쪽)
            'eyeLookDownRight': 0.4,     # 시선 아래 (오른쪽)
            'eyeBlinkLeft': 0.3,         # 눈꺼풀 처짐 (왼쪽)
            'eyeBlinkRight': 0.3,        # 눈꺼풀 처짐 (오른쪽)
        }
    }

    # 감지기 초기화
    detector = FacialFeatureDetector()

    # 슬픔 특징 분석
    print("\n슬픔 표정 분석:")
    result = detector.analyze_sadness_features(test_data_sadness)

    print(f"\n총점: {result['total_score']:.1f}/100")
    print(f"슬픔 판정: {'예' if result['is_sadness'] else '아니오'}")
    print(f"신뢰도: {result['confidence']:.2%}")

    print("\n감지된 특징:")
    for feature_name in result['detected_features']:
        feature_info = result['features'][feature_name]
        print(f"  - {feature_name}: {feature_info['value']:.2f} "
              f"(+{feature_info['score']}점)")

    print("\n모든 특징 상세:")
    for feature_name, feature_info in result['features'].items():
        status = "✓" if feature_info['detected'] else "✗"
        print(f"  {status} {feature_name:20s}: {feature_info['value']:.2f}")

    # 테스트 2: 슬픔이 아닌 경우
    print("\n" + "="*70)
    print("비슬픔 표정 테스트 (기쁨)")
    print("="*70)

    test_data_joy = {
        'vertices': [[0.1, 0.2, 0.3]] * 100,
        'blendshapes': {
            'mouthSmileLeft': 0.8,       # 입꼬리 올림
            'mouthSmileRight': 0.8,
            'cheekSquintLeft': 0.3,      # 뺨 올림 (웃을 때도)
            'cheekSquintRight': 0.3,
            'eyeWideLeft': 0.2,          # 눈 크게
            'eyeWideRight': 0.2,
        }
    }

    result_joy = detector.analyze_sadness_features(test_data_joy)
    print(f"\n총점: {result_joy['total_score']:.1f}/100")
    print(f"슬픔 판정: {'예' if result_joy['is_sadness'] else '아니오'}")
    print(f"신뢰도: {result_joy['confidence']:.2%}")
