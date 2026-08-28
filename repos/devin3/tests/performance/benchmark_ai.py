# Devin/tests/performance/benchmark_ai.py
# Purpose: A performance benchmark suite to measure and compare the latency
#          and throughput of various integrated LLM connectors.

import logging
import time
import os
from typing import List, Dict, Any

try:
    import numpy as np
    import tiktoken
    # --- Import the connectors we are going to test ---
    from modules.ai_connector import AIRequest, OpenAIConnector, GeminiConnector, PerplexityConnector
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AIBenchmark")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# --- Define the standard set of benchmark prompts ---
BENCHMARK_PROMPTS = {
    "Short Q&A": "What are the primary differences between TCP and UDP protocols?",
    "Code Generation": "Write a Python function that takes a list of integers and returns a new list containing only the prime numbers.",
    "Summarization": "Summarize the key events of the Apollo 11 moon landing mission in three concise paragraphs.",
    "Creative Writing": "Write a short, dramatic monologue from the perspective of a ship's AI watching its crew abandon it in a failing escape pod."
}

def run_benchmarks(connectors: Dict[str, Any], num_runs: int = 3) -> List[Dict]:
    """
    Runs a suite of benchmark prompts against a list of AI connectors.

    Args:
        connectors (Dict[str, Any]): A dictionary mapping provider names to connector instances.
        num_runs (int): The number of times to run each prompt to get an average.

    Returns:
        List[Dict]: A list of dictionaries containing the results.
    """
    results = []
    tokenizer = tiktoken.get_encoding("cl100k_base") # Standard tokenizer

    for provider_name, connector in connectors.items():
        for task_name, prompt in BENCHMARK_PROMPTS.items():
            logger.info(f"--- Benchmarking [{provider_name} / {task_name}] ---")
            latencies = []
            
            # Use a model appropriate for the provider
            model_name = "gpt-4o" if provider_name == "OpenAI" else \
                         "gemini-1.5-pro-latest" if provider_name == "Gemini" else \
                         "llama-3-sonar-large-32k-online"

            request = AIRequest(
                messages=[{"role": "user", "content": prompt}],
                model=model_name
            )

            response_content = ""
            for i in range(num_runs):
                logger.info(f"  Run {i+1}/{num_runs}...")
                start_time = time.perf_counter()
                response = connector.get_chat_completion(request)
                end_time = time.perf_counter()

                if response.is_success:
                    latencies.append(end_time - start_time)
                    response_content = response.content # Store content from the last successful run
                else:
                    logger.error(f"  API call failed for {provider_name}: {response.error_message}")
                    # Skip this benchmark if it fails consistently
                    if i == 0: latencies = []
                    break
            
            if not latencies:
                logger.error(f"  Skipping results for [{provider_name} / {task_name}] due to errors.")
                continue

            # Calculate statistics
            avg_latency = np.mean(latencies)
            std_dev = np.std(latencies)
            
            prompt_tokens = len(tokenizer.encode(prompt))
            completion_tokens = len(tokenizer.encode(response_content))
            tokens_per_second = completion_tokens / avg_latency if avg_latency > 0 else 0

            results.append({
                "provider": provider_name,
                "model": model_name,
                "task": task_name,
                "avg_latency_s": f"{avg_latency:.2f}",
                "std_dev_s": f"{std_dev:.2f}",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "tokens_per_second": f"{tokens_per_second:.1f}"
            })
            
    return results

def print_results_table(results: List[Dict]):
    """Prints the benchmark results in a clean, formatted table."""
    if not results:
        logger.warning("No benchmark results to display.")
        return
        
    # Sort results for consistent ordering
    results.sort(key=lambda x: (x['task'], x['provider']))
    
    headers = ["Provider", "Task", "Avg Latency (s)", "Tokens/Sec", "Prompt Tokens", "Completion Tokens", "Model"]
    
    # Calculate column widths
    col_widths = {h: len(h) for h in headers}
    for res in results:
        col_widths["Provider"] = max(col_widths["Provider"], len(res['provider']))
        col_widths["Task"] = max(col_widths["Task"], len(res['task']))
        col_widths["Model"] = max(col_widths["Model"], len(res['model']))

    # Print header
    header_line = " | ".join([h.ljust(col_widths[h]) for h in headers])
    separator_line = "-|-".join(["-" * col_widths[h] for h in headers])
    print("\n\n--- AI Performance Benchmark Results ---")
    print(header_line)
    print(separator_line)

    # Print rows
    for res in results:
        row = [
            res['provider'].ljust(col_widths["Provider"]),
            res['task'].ljust(col_widths["Task"]),
            res['avg_latency_s'].ljust(col_widths["Avg Latency (s)"]),
            res['tokens_per_second'].ljust(col_widths["Tokens/Sec"]),
            str(res['prompt_tokens']).ljust(col_widths["Prompt Tokens"]),
            str(res['completion_tokens']).ljust(col_widths["Completion Tokens"]),
            res['model'].ljust(col_widths["Model"])
        ]
        print(" | ".join(row))

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Performance Benchmark Suite ⏱️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing: {_import_error}")
    else:
        # --- 1. Load API keys from environment ---
        api_keys = {
            "OpenAI": os.getenv("OPENAI_API_KEY"),
            "Gemini": os.getenv("GEMINI_API_KEY"),
            "Perplexity": os.getenv("PERPLEXITY_API_KEY")
        }
        
        # --- 2. Initialize connectors for which keys are available ---
        connectors_to_test = {}
        if api_keys["OpenAI"]:
            connectors_to_test["OpenAI"] = OpenAIConnector(api_key=api_keys["OpenAI"])
        if api_keys["Gemini"]:
            connectors_to_test["Gemini"] = GeminiConnector(api_key=api_keys["Gemini"])
        if api_keys["Perplexity"]:
            connectors_to_test["Perplexity"] = PerplexityConnector(api_key=api_keys["Perplexity"])

        if not connectors_to_test:
            print("\nERROR: No AI provider API keys found in environment variables.")
            print("Please set at least one of: OPENAI_API_KEY, GEMINI_API_KEY, PERPLEXITY_API_KEY")
        else:
            print(f"Found credentials for: {list(connectors_to_test.keys())}")
            
            # --- 3. Run the benchmarks ---
            benchmark_results = run_benchmarks(connectors_to_test, num_runs=3)
            
            # --- 4. Display the results ---
            print_results_table(benchmark_results)

    print("\n=========================================================")
    print("=== AI Benchmark Suite Complete ===")
    print("=========================================================")
