"""
Rule-Based Emotion Classifier

ARKit BlendShapes를 사용한 규칙 기반 감정 분류기.
각 감정에 대한 표정 규칙을 정의하고 매칭합니다.

현재 구현된 감정:
- sadness (슬픔) - 완전 구현
- joy (기쁨) - 기본 규칙
- anger (분노) - 기본 규칙
- fear (공포) - 기본 규칙
- neutral (중립) - 기본 규칙
"""

import numpy as np
from typing import Dict, List, Tuple
from .facial_feature_detector import FacialFeatureDetector


class RuleBasedEmotionClassifier:
    """
    규칙 기반 감정 분류기
    """

    def __init__(self):
        """Initialize the classifier."""
        self.feature_detector = FacialFeatureDetector()

        # 감정 리스트
        self.emotions = [
            'neutral', 'joy', 'sadness', 'anger', 'fear',
            'disgust', 'surprise'
        ]

    def classify(self, face_data: Dict) -> Dict:
        """
        얼굴 데이터를 분석하여 감정 분류

        Args:
            face_data: 얼굴 메쉬 + BlendShapes 데이터

        Returns:
            분류 결과 딕셔너리
        """
        blendshapes = self.feature_detector.extract_blendshapes(face_data)

        if not blendshapes:
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'all_scores': {},
                'explanation': 'No blendshapes data found'
            }

        # 각 감정에 대한 점수 계산
        emotion_scores = {}

        emotion_scores['sadness'] = self._score_sadness(blendshapes)
        emotion_scores['joy'] = self._score_joy(blendshapes)
        emotion_scores['anger'] = self._score_anger(blendshapes)
        emotion_scores['fear'] = self._score_fear(blendshapes)
        emotion_scores['neutral'] = self._score_neutral(blendshapes)
        emotion_scores['disgust'] = self._score_disgust(blendshapes)
        emotion_scores['surprise'] = self._score_surprise(blendshapes)

        # 가장 높은 점수의 감정 선택
        best_emotion = max(emotion_scores, key=emotion_scores.get)
        best_score = emotion_scores[best_emotion]

        # 신뢰도 계산 (0.0 ~ 1.0)
        confidence = min(best_score / 100.0, 1.0)

        return {
            'emotion': best_emotion,
            'confidence': float(confidence),
            'score': float(best_score),
            'all_scores': {k: float(v) for k, v in emotion_scores.items()},
            'blendshapes': blendshapes
        }

    def _score_sadness(self, blendshapes: Dict) -> float:
        """
        슬픔 점수 계산 (완전 구현)

        특징:
        - 입 벌림
        - 입꼬리 내림
        - 뺨 올림
        - 반대 긴장
        - 시선 아래
        - 눈꺼풀 처짐
        """
        score = 0.0

        # 1. 입 벌림 (20점)
        jaw_open = blendshapes.get('jawOpen', 0.0)
        if jaw_open > 0.2:
            score += 20 * min(jaw_open / 0.5, 1.0)

        # 2. 입꼬리 내림 (25점)
        frown_left = blendshapes.get('mouthFrownLeft', 0.0)
        frown_right = blendshapes.get('mouthFrownRight', 0.0)
        avg_frown = (frown_left + frown_right) / 2.0
        if avg_frown > 0.3:
            score += 25 * min(avg_frown / 0.7, 1.0)

        # 3. 뺨 올림 (20점)
        cheek_left = blendshapes.get('cheekSquintLeft', 0.0)
        cheek_right = blendshapes.get('cheekSquintRight', 0.0)
        avg_cheek = (cheek_left + cheek_right) / 2.0
        if avg_cheek > 0.2:
            score += 20 * min(avg_cheek / 0.5, 1.0)

        # 4. 반대 긴장 (입꼬리 내림 + 뺨 올림 동시) (15점)
        if avg_frown > 0.15 and avg_cheek > 0.15:
            tension = min(avg_frown, avg_cheek)
            score += 15 * min(tension / 0.4, 1.0)

        # 5. 시선 아래 (10점)
        look_down_left = blendshapes.get('eyeLookDownLeft', 0.0)
        look_down_right = blendshapes.get('eyeLookDownRight', 0.0)
        avg_look_down = (look_down_left + look_down_right) / 2.0
        if avg_look_down > 0.3:
            score += 10 * min(avg_look_down / 0.6, 1.0)

        # 6. 눈꺼풀 처짐 (10점)
        blink_left = blendshapes.get('eyeBlinkLeft', 0.0)
        blink_right = blendshapes.get('eyeBlinkRight', 0.0)
        if 0.2 < blink_left < 0.6:
            score += 5
        if 0.2 < blink_right < 0.6:
            score += 5

        return score

    def _score_joy(self, blendshapes: Dict) -> float:
        """
        기쁨 점수 계산

        특징:
        - 입꼬리 올림 (웃음)
        - 뺨 올림 (눈 가늘게)
        - 눈 크게 뜨기
        """
        score = 0.0

        # 1. 입꼬리 올림 (40점)
        smile_left = blendshapes.get('mouthSmileLeft', 0.0)
        smile_right = blendshapes.get('mouthSmileRight', 0.0)
        avg_smile = (smile_left + smile_right) / 2.0
        if avg_smile > 0.3:
            score += 40 * min(avg_smile / 0.8, 1.0)

        # 2. 뺨 올림 (30점) - 진짜 웃음
        cheek_left = blendshapes.get('cheekSquintLeft', 0.0)
        cheek_right = blendshapes.get('cheekSquintRight', 0.0)
        avg_cheek = (cheek_left + cheek_right) / 2.0
        if avg_cheek > 0.2:
            score += 30 * min(avg_cheek / 0.6, 1.0)

        # 3. 입 + 뺨 동시 (20점) - Duchenne smile
        if avg_smile > 0.3 and avg_cheek > 0.2:
            score += 20

        # 4. 눈 밝게 (10점)
        eye_wide_left = blendshapes.get('eyeWideLeft', 0.0)
        eye_wide_right = blendshapes.get('eyeWideRight', 0.0)
        avg_eye_wide = (eye_wide_left + eye_wide_right) / 2.0
        if avg_eye_wide > 0.1:
            score += 10 * min(avg_eye_wide / 0.4, 1.0)

        return score

    def _score_anger(self, blendshapes: Dict) -> float:
        """
        분노 점수 계산

        특징:
        - 눈썹 내림
        - 입꼬리 내림
        - 입술 꽉 다물기
        - 코 주름
        """
        score = 0.0

        # 1. 눈썹 내림 (30점)
        brow_down_left = blendshapes.get('browDownLeft', 0.0)
        brow_down_right = blendshapes.get('browDownRight', 0.0)
        avg_brow_down = (brow_down_left + brow_down_right) / 2.0
        if avg_brow_down > 0.3:
            score += 30 * min(avg_brow_down / 0.7, 1.0)

        # 2. 입꼬리 내림 (25점)
        frown_left = blendshapes.get('mouthFrownLeft', 0.0)
        frown_right = blendshapes.get('mouthFrownRight', 0.0)
        avg_frown = (frown_left + frown_right) / 2.0
        if avg_frown > 0.2:
            score += 25 * min(avg_frown / 0.6, 1.0)

        # 3. 입 꽉 다물기 (25점)
        mouth_press = blendshapes.get('mouthPucker', 0.0)
        if mouth_press > 0.3:
            score += 25 * min(mouth_press / 0.7, 1.0)

        # 4. 코 주름 (20점)
        nose_sneer_left = blendshapes.get('noseSneerLeft', 0.0)
        nose_sneer_right = blendshapes.get('noseSneerRight', 0.0)
        avg_nose_sneer = (nose_sneer_left + nose_sneer_right) / 2.0
        if avg_nose_sneer > 0.2:
            score += 20 * min(avg_nose_sneer / 0.5, 1.0)

        return score

    def _score_fear(self, blendshapes: Dict) -> float:
        """
        공포 점수 계산

        특징:
        - 눈 크게 뜨기
        - 눈썹 올리기
        - 입 벌리기
        """
        score = 0.0

        # 1. 눈 크게 뜨기 (35점)
        eye_wide_left = blendshapes.get('eyeWideLeft', 0.0)
        eye_wide_right = blendshapes.get('eyeWideRight', 0.0)
        avg_eye_wide = (eye_wide_left + eye_wide_right) / 2.0
        if avg_eye_wide > 0.4:
            score += 35 * min(avg_eye_wide / 0.8, 1.0)

        # 2. 눈썹 올리기 (30점)
        brow_inner_up = blendshapes.get('browInnerUp', 0.0)
        brow_outer_left = blendshapes.get('browOuterUpLeft', 0.0)
        brow_outer_right = blendshapes.get('browOuterUpRight', 0.0)
        avg_brow_up = (brow_inner_up + brow_outer_left + brow_outer_right) / 3.0
        if avg_brow_up > 0.3:
            score += 30 * min(avg_brow_up / 0.7, 1.0)

        # 3. 입 벌리기 (25점)
        jaw_open = blendshapes.get('jawOpen', 0.0)
        if jaw_open > 0.3:
            score += 25 * min(jaw_open / 0.7, 1.0)

        # 4. 입 옆으로 늘어남 (10점)
        mouth_stretch = max(
            blendshapes.get('mouthLeft', 0.0),
            blendshapes.get('mouthRight', 0.0)
        )
        if mouth_stretch > 0.2:
            score += 10 * min(mouth_stretch / 0.5, 1.0)

        return score

    def _score_neutral(self, blendshapes: Dict) -> float:
        """
        중립 점수 계산

        특징: 모든 BlendShapes가 낮은 값
        """
        # 모든 BlendShapes의 평균 활성화 정도
        total_activation = sum(blendshapes.values())
        avg_activation = total_activation / len(blendshapes) if blendshapes else 0

        # 활성화가 낮을수록 중립
        if avg_activation < 0.1:
            score = 100 - (avg_activation * 1000)
        elif avg_activation < 0.2:
            score = 50 - (avg_activation * 250)
        else:
            score = max(0, 30 - (avg_activation * 100))

        return max(0, score)

    def _score_disgust(self, blendshapes: Dict) -> float:
        """
        혐오 점수 계산

        특징:
        - 코 주름
        - 윗입술 올리기
        - 입꼬리 내림
        """
        score = 0.0

        # 1. 코 주름 (40점)
        nose_sneer_left = blendshapes.get('noseSneerLeft', 0.0)
        nose_sneer_right = blendshapes.get('noseSneerRight', 0.0)
        avg_nose_sneer = (nose_sneer_left + nose_sneer_right) / 2.0
        if avg_nose_sneer > 0.3:
            score += 40 * min(avg_nose_sneer / 0.7, 1.0)

        # 2. 윗입술 올리기 (30점)
        upper_left = blendshapes.get('mouthUpperUpLeft', 0.0)
        upper_right = blendshapes.get('mouthUpperUpRight', 0.0)
        avg_upper = (upper_left + upper_right) / 2.0
        if avg_upper > 0.2:
            score += 30 * min(avg_upper / 0.6, 1.0)

        # 3. 입꼬리 내림 (20점)
        frown_left = blendshapes.get('mouthFrownLeft', 0.0)
        frown_right = blendshapes.get('mouthFrownRight', 0.0)
        avg_frown = (frown_left + frown_right) / 2.0
        if avg_frown > 0.2:
            score += 20 * min(avg_frown / 0.5, 1.0)

        # 4. 뺨 올림 (10점)
        cheek_left = blendshapes.get('cheekSquintLeft', 0.0)
        cheek_right = blendshapes.get('cheekSquintRight', 0.0)
        avg_cheek = (cheek_left + cheek_right) / 2.0
        if avg_cheek > 0.2:
            score += 10 * min(avg_cheek / 0.4, 1.0)

        return score

    def _score_surprise(self, blendshapes: Dict) -> float:
        """
        놀람 점수 계산

        특징:
        - 눈 크게 뜨기
        - 눈썹 올리기
        - 입 크게 벌리기
        """
        score = 0.0

        # 1. 입 크게 벌리기 (40점)
        jaw_open = blendshapes.get('jawOpen', 0.0)
        if jaw_open > 0.5:
            score += 40 * min(jaw_open / 0.9, 1.0)

        # 2. 눈 크게 뜨기 (30점)
        eye_wide_left = blendshapes.get('eyeWideLeft', 0.0)
        eye_wide_right = blendshapes.get('eyeWideRight', 0.0)
        avg_eye_wide = (eye_wide_left + eye_wide_right) / 2.0
        if avg_eye_wide > 0.3:
            score += 30 * min(avg_eye_wide / 0.7, 1.0)

        # 3. 눈썹 올리기 (30점)
        brow_inner_up = blendshapes.get('browInnerUp', 0.0)
        brow_outer_left = blendshapes.get('browOuterUpLeft', 0.0)
        brow_outer_right = blendshapes.get('browOuterUpRight', 0.0)
        avg_brow_up = (brow_inner_up + brow_outer_left + brow_outer_right) / 3.0
        if avg_brow_up > 0.3:
            score += 30 * min(avg_brow_up / 0.7, 1.0)

        return score


if __name__ == "__main__":
    # 테스트
    print("="*70)
    print("규칙 기반 감정 분류기 테스트")
    print("="*70)

    classifier = RuleBasedEmotionClassifier()

    # 테스트 1: 슬픔
    print("\n[테스트 1: 슬픔 표정]")
    sad_data = {
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

    result = classifier.classify(sad_data)
    print(f"예측 감정: {result['emotion']}")
    print(f"신뢰도: {result['confidence']:.2%}")
    print(f"점수: {result['score']:.1f}")
    print("\n모든 감정 점수:")
    for emotion, score in sorted(result['all_scores'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {emotion:12s}: {score:5.1f}")

    # 테스트 2: 기쁨
    print("\n" + "="*70)
    print("[테스트 2: 기쁨 표정]")
    joy_data = {
        'blendshapes': {
            'mouthSmileLeft': 0.8,
            'mouthSmileRight': 0.8,
            'cheekSquintLeft': 0.5,
            'cheekSquintRight': 0.5,
            'eyeWideLeft': 0.2,
            'eyeWideRight': 0.2,
        }
    }

    result = classifier.classify(joy_data)
    print(f"예측 감정: {result['emotion']}")
    print(f"신뢰도: {result['confidence']:.2%}")
    print(f"점수: {result['score']:.1f}")

    # 테스트 3: 중립
    print("\n" + "="*70)
    print("[테스트 3: 중립 표정]")
    neutral_data = {
        'blendshapes': {key: 0.05 for key in [
            'jawOpen', 'mouthSmileLeft', 'mouthSmileRight',
            'eyeBlinkLeft', 'eyeBlinkRight'
        ]}
    }

    result = classifier.classify(neutral_data)
    print(f"예측 감정: {result['emotion']}")
    print(f"신뢰도: {result['confidence']:.2%}")
    print(f"점수: {result['score']:.1f}")
