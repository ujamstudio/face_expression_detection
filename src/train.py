"""
Training script for Tri-Modal Emotion Classification Model

This script handles:
1. Loading configuration
2. Creating datasets
3. Building model
4. Training with callbacks
5. Evaluation
6. Saving model

Usage:
    python src/train.py --config configs/model_config.yaml
"""

import argparse
import yaml
from pathlib import Path
import tensorflow as tf
from datetime import datetime

from models.tri_modal_fusion import build_tri_modal_model, TriModalFusionModel
from data.dataset_loader import TriModalDataset
from utils.evaluation import EmotionEvaluator


def load_config(config_path):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def create_callbacks(log_dir, checkpoint_dir, patience=15):
    """
    Create training callbacks.

    Args:
        log_dir: Directory for TensorBoard logs
        checkpoint_dir: Directory for model checkpoints
        patience: Early stopping patience

    Returns:
        List of callbacks
    """
    callbacks = [
        # TensorBoard
        tf.keras.callbacks.TensorBoard(
            log_dir=log_dir,
            histogram_freq=1,
            write_graph=True
        ),

        # Model checkpointing (save best model)
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_dir / 'best_model.keras'),
            monitor='val_accuracy',
            save_best_only=True,
            mode='max',
            verbose=1
        ),

        # Early stopping
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=patience,
            restore_best_weights=True,
            verbose=1
        ),

        # Reduce learning rate on plateau
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        ),

        # CSV logger
        tf.keras.callbacks.CSVLogger(
            filename=str(log_dir / 'training_log.csv'),
            append=False
        )
    ]

    return callbacks


def train(config_path='configs/model_config.yaml'):
    """
    Main training function.

    Args:
        config_path: Path to configuration file
    """
    # Load configuration
    print("="*70)
    print("TRI-MODAL EMOTION CLASSIFICATION - TRAINING")
    print("="*70)

    config = load_config(config_path)
    print(f"\nConfiguration loaded from {config_path}")

    # Load emotion labels
    emotions_config_path = Path(config_path).parent / 'emotions.yaml'
    with open(emotions_config_path, 'r') as f:
        emotions_config = yaml.safe_load(f)

    emotion_to_label = {name: int(idx) for idx, name in emotions_config['emotions'].items()}
    label_to_emotion = {v: k for k, v in emotion_to_label.items()}

    print(f"Number of emotion classes: {len(emotion_to_label)}")

    # Create output directories
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(config['paths']['models']) / f'run_{timestamp}'
    log_dir = output_dir / 'logs'
    checkpoint_dir = output_dir / 'checkpoints'

    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(exist_ok=True)
    checkpoint_dir.mkdir(exist_ok=True)

    print(f"Output directory: {output_dir}")

    # Initialize dataset loader
    print("\n" + "="*70)
    print("LOADING DATASETS")
    print("="*70)

    dataset_loader = TriModalDataset(
        data_root=config['paths']['processed_data'],
        emotion_to_label=emotion_to_label,
        tokenizer_name=config['text']['model_name'],
        max_text_length=config['text']['max_length'],
        num_points=config['vision']['num_points'],
        spec_size=(config['audio']['spec_height'], config['audio']['spec_width'])
    )

    # Create datasets
    batch_size = config['training']['batch_size']

    train_dataset = dataset_loader.create_dataset(
        split='train',
        batch_size=batch_size,
        shuffle=True
    )

    val_dataset = dataset_loader.create_dataset(
        split='val',
        batch_size=batch_size,
        shuffle=False
    )

    test_dataset = dataset_loader.create_dataset(
        split='test',
        batch_size=batch_size,
        shuffle=False
    )

    # Build model
    print("\n" + "="*70)
    print("BUILDING MODEL")
    print("="*70)

    fusion_model_obj = TriModalFusionModel(config_path=config_path)
    model = fusion_model_obj.build_model()
    model = fusion_model_obj.compile_model(
        learning_rate=config['training']['learning_rate']
    )

    print("\nModel built successfully!")
    model.summary()

    # Create callbacks
    callbacks = create_callbacks(
        log_dir=log_dir,
        checkpoint_dir=checkpoint_dir,
        patience=config['training']['patience']
    )

    # Train model
    print("\n" + "="*70)
    print("TRAINING MODEL")
    print("="*70)

    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config['training']['epochs'],
        callbacks=callbacks,
        verbose=1
    )

    # Evaluate on test set
    print("\n" + "="*70)
    print("EVALUATING MODEL")
    print("="*70)

    # Get predictions
    y_true = []
    y_pred = []

    for batch_inputs, batch_labels in test_dataset:
        predictions = model.predict(batch_inputs, verbose=0)
        pred_labels = tf.argmax(predictions, axis=1).numpy()

        y_true.extend(batch_labels.numpy())
        y_pred.extend(pred_labels)

    # Evaluate
    evaluator = EmotionEvaluator(label_to_emotion)
    metrics = evaluator.evaluate(
        y_true=y_true,
        y_pred=y_pred,
        output_dir=output_dir / 'evaluation',
        show_plots=False
    )

    # Save final model
    final_model_path = output_dir / 'final_model.keras'
    model.save(final_model_path)
    print(f"\nFinal model saved to {final_model_path}")

    # Save training history
    import json
    history_path = output_dir / 'training_history.json'
    history_dict = {
        'loss': [float(x) for x in history.history['loss']],
        'accuracy': [float(x) for x in history.history['accuracy']],
        'val_loss': [float(x) for x in history.history['val_loss']],
        'val_accuracy': [float(x) for x in history.history['val_accuracy']]
    }
    with open(history_path, 'w') as f:
        json.dump(history_dict, f, indent=2)

    print(f"Training history saved to {history_path}")

    # Print final results
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"Best validation accuracy: {max(history.history['val_accuracy']):.4f}")
    print(f"Test accuracy: {metrics['accuracy']:.4f}")
    print(f"\nAll results saved to: {output_dir}")

    return model, history, metrics


def fine_tune(model_path, config_path='configs/model_config.yaml', epochs=10):
    """
    Fine-tune a trained model by unfreezing BERT.

    Args:
        model_path: Path to saved model
        config_path: Path to configuration file
        epochs: Number of fine-tuning epochs

    Returns:
        Fine-tuned model
    """
    print("\n" + "="*70)
    print("FINE-TUNING MODEL (Unfreezing BERT)")
    print("="*70)

    # Load configuration
    config = load_config(config_path)

    # Load model
    model = tf.keras.models.load_model(model_path)
    print(f"Model loaded from {model_path}")

    # Unfreeze BERT layers
    for layer in model.layers:
        if 'bert' in layer.name.lower():
            layer.trainable = True
            print(f"Unfroze layer: {layer.name}")

    # Recompile with lower learning rate
    finetune_lr = config['training']['finetune_learning_rate']
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=finetune_lr),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    print(f"Model recompiled with learning rate: {finetune_lr}")

    # Load datasets
    emotions_config_path = Path(config_path).parent / 'emotions.yaml'
    with open(emotions_config_path, 'r') as f:
        emotions_config = yaml.safe_load(f)

    emotion_to_label = {name: int(idx) for idx, name in emotions_config['emotions'].items()}

    dataset_loader = TriModalDataset(
        data_root=config['paths']['processed_data'],
        emotion_to_label=emotion_to_label,
        tokenizer_name=config['text']['model_name'],
        max_text_length=config['text']['max_length'],
        num_points=config['vision']['num_points'],
        spec_size=(config['audio']['spec_height'], config['audio']['spec_width'])
    )

    train_dataset = dataset_loader.create_dataset(
        split='train',
        batch_size=config['training']['batch_size'],
        shuffle=True
    )

    val_dataset = dataset_loader.create_dataset(
        split='val',
        batch_size=config['training']['batch_size'],
        shuffle=False
    )

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(config['paths']['models']) / f'finetune_{timestamp}'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fine-tune
    callbacks = create_callbacks(
        log_dir=output_dir / 'logs',
        checkpoint_dir=output_dir / 'checkpoints',
        patience=5
    )

    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1
    )

    # Save fine-tuned model
    finetuned_path = output_dir / 'finetuned_model.keras'
    model.save(finetuned_path)
    print(f"\nFine-tuned model saved to {finetuned_path}")

    return model, history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train tri-modal emotion classification model')
    parser.add_argument(
        '--config',
        type=str,
        default='configs/model_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--finetune',
        type=str,
        default=None,
        help='Path to model for fine-tuning'
    )
    parser.add_argument(
        '--finetune-epochs',
        type=int,
        default=10,
        help='Number of fine-tuning epochs'
    )

    args = parser.parse_args()

    if args.finetune:
        # Fine-tune existing model
        fine_tune(
            model_path=args.finetune,
            config_path=args.config,
            epochs=args.finetune_epochs
        )
    else:
        # Train from scratch
        train(config_path=args.config)
