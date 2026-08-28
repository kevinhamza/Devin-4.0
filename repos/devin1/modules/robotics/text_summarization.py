"""
Text Summarization Module for Robotics
Summarizes long texts using advanced NLP techniques.
"""

from typing import List, Tuple
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

class TextSummarizer:
    """
    Provides functionalities for summarizing long texts using pretrained NLP models.
    """

    def __init__(self, model_name: str = "t5-small"):
        """
        Initialize the text summarization model.
        
        Args:
            model_name (str): The name of the pretrained summarization model to use.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.summarizer = pipeline("summarization", model=self.model, tokenizer=self.tokenizer)

    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 50, do_sample: bool = False) -> str:
        """
        Summarize a given text.
        
        Args:
            text (str): The text to summarize.
            max_length (int): The maximum length of the summary.
            min_length (int): The minimum length of the summary.
            do_sample (bool): Whether to sample during text generation.
        
        Returns:
            str: The summarized text.
        """
        if len(text.strip()) == 0:
            raise ValueError("Input text cannot be empty.")

        summary = self.summarizer(
            text, 
            max_length=max_length, 
            min_length=min_length, 
            do_sample=do_sample
        )
        return summary[0]['summary_text']

    def batch_summarize(self, texts: List[str], max_length: int = 150, min_length: int = 50) -> List[str]:
        """
        Summarize a batch of texts.
        
        Args:
            texts (List[str]): A list of texts to summarize.
            max_length (int): The maximum length of each summary.
            min_length (int): The minimum length of each summary.
        
        Returns:
            List[str]: A list of summarized texts.
        """
        summaries = []
        for text in texts:
            try:
                summaries.append(self.summarize_text(text, max_length, min_length))
            except ValueError as e:
                summaries.append(f"Error: {str(e)}")
        return summaries

    def summarize_paragraphs(self, paragraphs: List[str], merge: bool = True) -> str:
        """
        Summarize multiple paragraphs and optionally merge them into one summary.
        
        Args:
            paragraphs (List[str]): A list of paragraphs to summarize.
            merge (bool): Whether to merge all summaries into one.
        
        Returns:
            str: The merged summary if merge=True, otherwise a list of summaries.
        """
        summarized_paragraphs = self.batch_summarize(paragraphs)
        if merge:
            return " ".join(summarized_paragraphs)
        return summarized_paragraphs


# Example Usage
if __name__ == "__main__":
    summarizer = TextSummarizer(model_name="facebook/bart-large-cnn")
    
    long_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence 
    displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize its chance of achieving its goals. 
    Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic 
    "cognitive" functions that humans associate with the human mind, such as "learning" and "problem-solving".
    """
    
    print("Single Text Summary:")
    print(summarizer.summarize_text(long_text, max_length=100, min_length=30))

    paragraphs = [
        "Artificial intelligence is rapidly advancing, influencing numerous industries.",
        "The use of AI in robotics is growing, with applications in manufacturing, healthcare, and exploration."
    ]
    
    print("\nBatch Summary:")
    print(summarizer.batch_summarize(paragraphs, max_length=50, min_length=20))

    print("\nMerged Summary:")
    print(summarizer.summarize_paragraphs(paragraphs))
