#!/usr/bin/env python3
"""
Evaluation script for InvestoChat RAG system.

Tests retrieval accuracy across multiple query types and tracks improvements over time.

Usage:
    python evaluate.py                          # Run all tests
    python evaluate.py --category payment       # Test only payment queries
    python evaluate.py --save results.json      # Save detailed results
    python evaluate.py --verbose                # Show detailed output
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from dotenv import load_dotenv
from main import retrieve, rag

load_dotenv()

# Configuration
WORKSPACE = Path(__file__).parent / "workspace"
TEST_QUERIES_PATH = WORKSPACE / "test_queries.json"
RESULTS_DIR = WORKSPACE / "eval_results"


def load_test_queries() -> Dict[str, Any]:
    """Load test queries from JSON file."""
    if not TEST_QUERIES_PATH.exists():
        raise FileNotFoundError(f"Test queries file not found: {TEST_QUERIES_PATH}")

    with open(TEST_QUERIES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_query(query_data: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Evaluate a single query.

    Args:
        query_data: Query specification from test_queries.json
        verbose: Print detailed output

    Returns:
        Evaluation results dictionary
    """
    query_id = query_data["id"]
    query = query_data["query"]
    category = query_data["category"]
    project_id = query_data.get("project_id")
    expected_mode = query_data.get("expected_mode")
    expected_min_score = query_data.get("expected_min_score", 0.0)
    expected_keywords = query_data.get("expected_keywords", [])

    if verbose:
        print(f"\n{'='*80}")
        print(f"Query {query_id}: {query}")
        print(f"Category: {category}, Project: {project_id or 'All'}")
        print(f"{'='*80}")

    # Run retrieval
    try:
        result = retrieve(query, k=3, project_id=project_id)
        mode = result.get("mode", "empty")
        answers = result.get("answers", [])
        metas = result.get("metas", [])

        # Extract scores
        scores = [m.get("score", 0.0) for m in metas if m.get("score") is not None]
        top_score = max(scores) if scores else 0.0
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Check keyword presence
        combined_text = " ".join(answers).lower()
        keywords_found = [kw for kw in expected_keywords if kw.lower() in combined_text]
        keyword_coverage = len(keywords_found) / len(expected_keywords) if expected_keywords else 1.0

        # Determine if test passed
        mode_match = mode == expected_mode if expected_mode else True
        score_ok = top_score >= expected_min_score
        keyword_ok = keyword_coverage >= 0.5  # At least 50% of expected keywords

        passed = mode_match and score_ok and keyword_ok

        if verbose:
            print(f"  Mode: {mode} (expected: {expected_mode}) {'✓' if mode_match else '✗'}")
            print(f"  Top Score: {top_score:.3f} (min: {expected_min_score}) {'✓' if score_ok else '✗'}")
            print(f"  Keywords: {len(keywords_found)}/{len(expected_keywords)} {'✓' if keyword_ok else '✗'}")
            print(f"  Found: {keywords_found}")
            print(f"  Status: {'PASS ✓' if passed else 'FAIL ✗'}")

            if answers:
                print(f"\n  Retrieved {len(answers)} chunks:")
                for i, (ans, meta) in enumerate(zip(answers, metas), 1):
                    snippet = ans[:200].replace('\n', ' ')
                    score = meta.get('score', 0)
                    source = meta.get('source', 'unknown')
                    page = meta.get('page', '?')
                    print(f"    {i}. {source} p.{page} (score: {score:.3f})")
                    print(f"       {snippet}...")

        return {
            "query_id": query_id,
            "query": query,
            "category": category,
            "passed": passed,
            "mode": mode,
            "expected_mode": expected_mode,
            "mode_match": mode_match,
            "top_score": top_score,
            "avg_score": avg_score,
            "expected_min_score": expected_min_score,
            "score_ok": score_ok,
            "keywords_found": keywords_found,
            "keyword_coverage": keyword_coverage,
            "keyword_ok": keyword_ok,
            "num_results": len(answers),
        }

    except Exception as e:
        print(f"  ERROR: {e}")
        return {
            "query_id": query_id,
            "query": query,
            "category": category,
            "passed": False,
            "error": str(e),
        }


def print_summary(results: List[Dict[str, Any]], test_data: Dict[str, Any]):
    """Print evaluation summary."""
    total = len(results)
    passed = sum(1 for r in results if r.get("passed", False))
    failed = total - passed

    # Category breakdown
    category_stats = {}
    for result in results:
        cat = result["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0}
        category_stats[cat]["total"] += 1
        if result.get("passed", False):
            category_stats[cat]["passed"] += 1

    # Mode accuracy
    mode_stats = {}
    for result in results:
        mode = result.get("mode")
        expected = result.get("expected_mode")
        if expected:
            if expected not in mode_stats:
                mode_stats[expected] = {"total": 0, "correct": 0}
            mode_stats[expected]["total"] += 1
            if result.get("mode_match", False):
                mode_stats[expected]["correct"] += 1

    # Score statistics
    scores = [r.get("top_score", 0) for r in results if "top_score" in r]
    avg_top_score = sum(scores) / len(scores) if scores else 0.0

    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"\nOverall: {passed}/{total} queries passed ({passed/total*100:.1f}%)")
    print(f"  ✓ Passed: {passed}")
    print(f"  ✗ Failed: {failed}")
    print(f"  Average Top Score: {avg_top_score:.3f}")

    print(f"\nBy Category:")
    for cat, stats in sorted(category_stats.items()):
        pct = stats["passed"] / stats["total"] * 100
        print(f"  {cat:20s}: {stats['passed']:2d}/{stats['total']:2d} ({pct:5.1f}%)")

    print(f"\nMode Accuracy:")
    for mode, stats in sorted(mode_stats.items()):
        pct = stats["correct"] / stats["total"] * 100
        print(f"  {mode:20s}: {stats['correct']:2d}/{stats['total']:2d} ({pct:5.1f}%)")

    print("\n" + "="*80)


def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save detailed results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(results),
        "passed": sum(1 for r in results if r.get("passed", False)),
        "failed": sum(1 for r in results if not r.get("passed", False)),
        "results": results,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate InvestoChat RAG system")
    parser.add_argument("--category", type=str, help="Test only specific category")
    parser.add_argument("--query-id", type=int, help="Test only specific query ID")
    parser.add_argument("--save", type=str, help="Save results to file (e.g., results.json)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    # Load test queries
    test_data = load_test_queries()
    queries = test_data["queries"]

    # Filter queries if needed
    if args.category:
        queries = [q for q in queries if q["category"] == args.category]
        print(f"Testing category: {args.category} ({len(queries)} queries)")

    if args.query_id:
        queries = [q for q in queries if q["id"] == args.query_id]
        print(f"Testing query ID: {args.query_id}")

    if not queries:
        print("No queries match the filters!")
        return

    # Run evaluation
    print(f"\nRunning evaluation on {len(queries)} queries...")
    print("="*80)

    results = []
    for query_data in queries:
        result = evaluate_query(query_data, verbose=args.verbose)
        results.append(result)

        # Show progress in non-verbose mode
        if not args.verbose:
            status = "✓" if result.get("passed", False) else "✗"
            print(f"  {status} Query {result['query_id']:2d}: {result['query'][:60]}")

    # Print summary
    print_summary(results, test_data)

    # Save results if requested
    if args.save:
        output_path = RESULTS_DIR / args.save
        save_results(results, output_path)


if __name__ == "__main__":
    main()
