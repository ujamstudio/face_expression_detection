"""
Models module for tri-modal emotion classification.
"""

try:
    from .pointnet import build_pointnet_branch, normalize_point_cloud
    from .audio_cnn import build_audio_cnn_branch, build_audio_cnn_deeper
    from .text_encoder import build_text_encoder_branch, get_tokenizer, tokenize_text
    from .tri_modal_fusion import TriModalFusionModel, build_tri_modal_model
except Exception:
    pass

from .rule_based_classifier import RuleBasedEmotionClassifier

__all__ = [
    'build_pointnet_branch',
    'normalize_point_cloud',
    'build_audio_cnn_branch',
    'build_audio_cnn_deeper',
    'build_text_encoder_branch',
    'get_tokenizer',
    'tokenize_text',
    'TriModalFusionModel',
    'build_tri_modal_model',
    'RuleBasedEmotionClassifier',
]
