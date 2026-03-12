"""
Text Encoder using BERT for Context Understanding

This module uses pre-trained BERT to extract semantic features from
transcribed speech. The [CLS] token embedding captures the contextual
meaning of the entire utterance.

Transfer Learning Strategy:
1. Initial training: Freeze BERT weights
2. Fine-tuning phase: Unfreeze with very low learning rate
"""

import tensorflow as tf
from tensorflow.keras import layers, models
from transformers import TFBertModel, BertTokenizer, BertConfig


def build_text_encoder_branch(
    model_name="bert-base-uncased",
    max_length=128,
    freeze_bert=True,
    name="text_encoder"
):
    """
    Build BERT-based text encoder for extracting contextual features.

    Architecture:
        Input: Token IDs (max_length,) + Attention Mask (max_length,)
        → BERT Model
        → [CLS] Token Output (pooler_output)
        → Output: (768,) feature vector

    Args:
        model_name: HuggingFace model name (default: "bert-base-uncased")
        max_length: Maximum sequence length (default: 128)
        freeze_bert: Whether to freeze BERT weights initially (default: True)
        name: Name prefix for the branch

    Returns:
        Keras Model with dict inputs and feature vector output
    """
    # Input layers
    input_ids = layers.Input(
        shape=(max_length,),
        dtype=tf.int32,
        name=f"{name}_input_ids"
    )
    attention_mask = layers.Input(
        shape=(max_length,),
        dtype=tf.int32,
        name=f"{name}_attention_mask"
    )

    # Load pre-trained BERT
    try:
        bert_model = TFBertModel.from_pretrained(
            model_name,
            from_pt=False  # Try TensorFlow checkpoint first
        )
        print(f"Loaded BERT model: {model_name}")
    except Exception as e:
        print(f"Failed to load {model_name}, trying PyTorch checkpoint: {e}")
        try:
            bert_model = TFBertModel.from_pretrained(
                model_name,
                from_pt=True  # Convert from PyTorch if necessary
            )
        except Exception as e2:
            print(f"Failed to load BERT: {e2}")
            print("Using random initialization (for testing only)")
            config = BertConfig()
            bert_model = TFBertModel(config)

    # Set trainability
    bert_model.trainable = not freeze_bert
    if freeze_bert:
        print(f"BERT weights frozen for transfer learning")
    else:
        print(f"BERT weights unfrozen for fine-tuning")

    # Get BERT outputs
    bert_output = bert_model(
        input_ids=input_ids,
        attention_mask=attention_mask
    )

    # Use [CLS] token representation (pooler_output)
    # This is the contextualized representation of the entire sequence
    text_features = bert_output.pooler_output  # Shape: (batch, 768)

    # Create model
    model = models.Model(
        inputs={
            "input_ids": input_ids,
            "attention_mask": attention_mask
        },
        outputs=text_features,
        name=name
    )

    return model, bert_model


def get_tokenizer(model_name="bert-base-uncased"):
    """
    Load BERT tokenizer.

    Args:
        model_name: HuggingFace model name

    Returns:
        BertTokenizer instance
    """
    tokenizer = BertTokenizer.from_pretrained(model_name)
    return tokenizer


def tokenize_text(text, tokenizer, max_length=128):
    """
    Tokenize text for BERT input.

    Args:
        text: Input text string or list of strings
        tokenizer: BertTokenizer instance
        max_length: Maximum sequence length

    Returns:
        Dictionary with 'input_ids' and 'attention_mask'
    """
    encoded = tokenizer(
        text,
        padding='max_length',
        truncation=True,
        max_length=max_length,
        return_tensors='tf'
    )
    return {
        'input_ids': encoded['input_ids'],
        'attention_mask': encoded['attention_mask']
    }


def unfreeze_bert_for_finetuning(bert_model, num_layers_to_unfreeze=-1):
    """
    Unfreeze BERT layers for fine-tuning.

    Args:
        bert_model: TFBertModel instance
        num_layers_to_unfreeze: Number of encoder layers to unfreeze from the top
                                 -1 means unfreeze all layers (default)

    Returns:
        None (modifies bert_model in-place)
    """
    bert_model.trainable = True

    if num_layers_to_unfreeze == -1:
        # Unfreeze all
        print("Unfreezing all BERT layers")
    else:
        # Freeze embedding and early layers
        bert_model.bert.embeddings.trainable = False

        # Unfreeze only top N encoder layers
        num_encoder_layers = len(bert_model.bert.encoder.layer)
        for i, layer in enumerate(bert_model.bert.encoder.layer):
            if i < (num_encoder_layers - num_layers_to_unfreeze):
                layer.trainable = False
            else:
                layer.trainable = True

        print(f"Unfroze top {num_layers_to_unfreeze} BERT encoder layers")


if __name__ == "__main__":
    # Test the Text Encoder branch
    print("Building Text Encoder branch...")
    text_encoder, bert_model = build_text_encoder_branch(
        model_name="bert-base-uncased",
        max_length=128,
        freeze_bert=True
    )
    text_encoder.summary()

    # Test tokenization
    print("\n" + "="*50)
    print("Testing tokenization...")
    tokenizer = get_tokenizer("bert-base-uncased")

    test_texts = [
        "I feel so disappointed about the results.",
        "This makes me incredibly happy!",
        "I'm not sure how to feel about this situation.",
        "I deeply regret not taking that opportunity."
    ]

    encoded = tokenize_text(test_texts, tokenizer, max_length=128)
    print(f"Input IDs shape: {encoded['input_ids'].shape}")
    print(f"Attention Mask shape: {encoded['attention_mask'].shape}")

    # Test forward pass
    print("\n" + "="*50)
    print("Testing forward pass...")
    output = text_encoder.predict(encoded)
    print(f"Output shape: {output.shape}")
    print(f"Output feature vector (first sample): {output[0][:10]}...")

    # Test unfreezing
    print("\n" + "="*50)
    print("Testing fine-tuning setup...")
    unfreeze_bert_for_finetuning(bert_model, num_layers_to_unfreeze=2)
    print(f"BERT trainable: {bert_model.trainable}")
