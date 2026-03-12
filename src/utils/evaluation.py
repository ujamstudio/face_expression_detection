"""
Evaluation utilities for emotion classification model.

Includes confusion matrix visualization, per-class metrics, and error analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_recall_fscore_support
)
import pandas as pd


class EmotionEvaluator:
    """
    Evaluate emotion classification model performance.
    """

    def __init__(self, emotion_labels):
        """
        Initialize evaluator.

        Args:
            emotion_labels: Dictionary mapping label indices to emotion names
                           e.g., {0: 'neutral', 1: 'joy', ...}
        """
        self.emotion_labels = emotion_labels
        self.num_classes = len(emotion_labels)

    def compute_metrics(self, y_true, y_pred):
        """
        Compute comprehensive evaluation metrics.

        Args:
            y_true: True labels (numpy array)
            y_pred: Predicted labels (numpy array)

        Returns:
            Dictionary of metrics
        """
        # Overall accuracy
        accuracy = accuracy_score(y_true, y_pred)

        # Per-class precision, recall, F1
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=list(range(self.num_classes)),
            zero_division=0
        )

        # Confusion matrix
        cm = confusion_matrix(
            y_true,
            y_pred,
            labels=list(range(self.num_classes))
        )

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support,
            'confusion_matrix': cm
        }

        return metrics

    def plot_confusion_matrix(
        self,
        confusion_mat,
        save_path=None,
        figsize=(12, 10),
        cmap='Blues'
    ):
        """
        Plot confusion matrix heatmap.

        Args:
            confusion_mat: Confusion matrix (2D numpy array)
            save_path: Path to save figure (optional)
            figsize: Figure size
            cmap: Colormap

        Returns:
            Matplotlib figure
        """
        # Normalize confusion matrix (percentages)
        cm_normalized = confusion_mat.astype('float') / (
            confusion_mat.sum(axis=1)[:, np.newaxis] + 1e-8
        )

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Plot heatmap
        sns.heatmap(
            cm_normalized,
            annot=True,
            fmt='.2f',
            cmap=cmap,
            xticklabels=[self.emotion_labels[i] for i in range(self.num_classes)],
            yticklabels=[self.emotion_labels[i] for i in range(self.num_classes)],
            ax=ax,
            cbar_kws={'label': 'Normalized Frequency'}
        )

        ax.set_xlabel('Predicted Emotion', fontsize=12)
        ax.set_ylabel('True Emotion', fontsize=12)
        ax.set_title('Emotion Classification Confusion Matrix', fontsize=14, fontweight='bold')

        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Confusion matrix saved to {save_path}")

        return fig

    def print_classification_report(self, y_true, y_pred):
        """
        Print detailed classification report.

        Args:
            y_true: True labels
            y_pred: Predicted labels
        """
        target_names = [self.emotion_labels[i] for i in range(self.num_classes)]

        report = classification_report(
            y_true,
            y_pred,
            labels=list(range(self.num_classes)),
            target_names=target_names,
            zero_division=0
        )

        print("="*70)
        print("CLASSIFICATION REPORT")
        print("="*70)
        print(report)

    def create_metrics_dataframe(self, metrics):
        """
        Create pandas DataFrame with per-emotion metrics.

        Args:
            metrics: Dictionary from compute_metrics()

        Returns:
            pandas DataFrame
        """
        data = {
            'Emotion': [self.emotion_labels[i] for i in range(self.num_classes)],
            'Precision': metrics['precision'],
            'Recall': metrics['recall'],
            'F1-Score': metrics['f1'],
            'Support': metrics['support']
        }

        df = pd.DataFrame(data)
        df = df.sort_values('F1-Score', ascending=False)

        return df

    def analyze_errors(self, y_true, y_pred, top_n=5):
        """
        Analyze most common classification errors.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            top_n: Number of top error pairs to return

        Returns:
            List of tuples: (true_emotion, predicted_emotion, count)
        """
        cm = confusion_matrix(
            y_true,
            y_pred,
            labels=list(range(self.num_classes))
        )

        # Find off-diagonal elements (errors)
        errors = []
        for i in range(self.num_classes):
            for j in range(self.num_classes):
                if i != j and cm[i, j] > 0:
                    errors.append((
                        self.emotion_labels[i],
                        self.emotion_labels[j],
                        cm[i, j]
                    ))

        # Sort by count
        errors.sort(key=lambda x: x[2], reverse=True)

        return errors[:top_n]

    def plot_per_emotion_performance(self, metrics, save_path=None, figsize=(14, 6)):
        """
        Plot bar chart of per-emotion F1 scores.

        Args:
            metrics: Dictionary from compute_metrics()
            save_path: Path to save figure
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        df = self.create_metrics_dataframe(metrics)

        fig, ax = plt.subplots(figsize=figsize)

        # Plot F1 scores
        bars = ax.bar(
            range(len(df)),
            df['F1-Score'],
            color=['#1f77b4' if score >= 0.7 else '#ff7f0e' for score in df['F1-Score']]
        )

        ax.set_xlabel('Emotion', fontsize=12)
        ax.set_ylabel('F1-Score', fontsize=12)
        ax.set_title('Per-Emotion Classification Performance', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df['Emotion'], rotation=45, ha='right')
        ax.set_ylim(0, 1.0)
        ax.axhline(y=0.7, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Target (0.70)')
        ax.legend()

        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.02,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                fontsize=9
            )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Performance chart saved to {save_path}")

        return fig

    def evaluate(
        self,
        y_true,
        y_pred,
        output_dir=None,
        show_plots=True
    ):
        """
        Complete evaluation pipeline.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            output_dir: Directory to save results (optional)
            show_plots: Whether to display plots

        Returns:
            Dictionary of metrics
        """
        # Compute metrics
        metrics = self.compute_metrics(y_true, y_pred)

        # Print report
        self.print_classification_report(y_true, y_pred)

        # Print overall accuracy
        print(f"\nOverall Accuracy: {metrics['accuracy']:.4f}")

        # Print error analysis
        print("\n" + "="*70)
        print("TOP CLASSIFICATION ERRORS")
        print("="*70)
        errors = self.analyze_errors(y_true, y_pred, top_n=5)
        for true_emotion, pred_emotion, count in errors:
            print(f"  {true_emotion:15s} → {pred_emotion:15s}: {count:4d} times")

        # Create plots
        if output_dir:
            from pathlib import Path
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Confusion matrix
            cm_path = output_path / 'confusion_matrix.png'
            self.plot_confusion_matrix(metrics['confusion_matrix'], save_path=cm_path)

            # Performance chart
            perf_path = output_path / 'per_emotion_performance.png'
            self.plot_per_emotion_performance(metrics, save_path=perf_path)

            # Save metrics to CSV
            df = self.create_metrics_dataframe(metrics)
            csv_path = output_path / 'metrics.csv'
            df.to_csv(csv_path, index=False)
            print(f"\nMetrics saved to {csv_path}")

        if show_plots:
            plt.show()
        else:
            plt.close('all')

        return metrics


if __name__ == "__main__":
    # Example usage
    print("Emotion Evaluator Test\n" + "="*70)

    # Define emotion labels
    emotion_labels = {
        0: 'neutral',
        1: 'joy',
        2: 'sadness',
        3: 'anger',
        4: 'fear',
        5: 'disgust',
        6: 'surprise',
        7: 'regret'
    }

    # Generate synthetic predictions
    np.random.seed(42)
    num_samples = 200
    num_classes = len(emotion_labels)

    y_true = np.random.randint(0, num_classes, num_samples)
    y_pred = y_true.copy()

    # Add some errors
    error_indices = np.random.choice(num_samples, 50, replace=False)
    y_pred[error_indices] = np.random.randint(0, num_classes, 50)

    # Evaluate
    evaluator = EmotionEvaluator(emotion_labels)
    metrics = evaluator.evaluate(
        y_true,
        y_pred,
        output_dir='evaluation_results',
        show_plots=False
    )

    print("\n" + "="*70)
    print("Evaluation complete!")
