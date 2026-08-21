import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.agent import SupportAgent

class EvaluationRunner:
    def __init__(self):
        self.agent = SupportAgent()

    def run_case(self, case: Dict[str, Any], verbose: bool = True) -> Tuple[bool, List[str]]:
        case_id = case.get("id", "unknown")
        messages = case.get("messages", [])
        expect = case.get("expect", {})
        session_id = f"eval_{case_id}"
        
        # Reset session
        self.agent.session_manager.clear_session(session_id)
        
        last_result = None
        for msg in messages:
            if msg.get("role") == "user":
                last_result = self.agent.process_message(
                    user_message=msg.get("content", ""),
                    session_id=session_id,
                )

        if not last_result:
            return False, ["No response generated."]

        failures = []
        resp_text = last_result.get("response", "")
        resp_lower = resp_text.lower()
        sources = last_result.get("sources", [])
        tool_called = last_result.get("tool_called")
        tool_args = last_result.get("tool_arguments") or {}
        handoff = last_result.get("needs_handoff", False)

        # 1. must_include
        for req in expect.get("must_include", []):
            if req.lower() not in resp_lower:
                failures.append(f"Missing required phrase: '{req}'")

        # 2. must_not_include
        for forbidden in expect.get("must_not_include", []):
            if forbidden.lower() in resp_lower:
                failures.append(f"Forbidden phrase found: '{forbidden}'")

        # 3. must_include_concepts
        for concept in expect.get("must_include_concepts", []):
            # Check keywords in concept
            concept_words = [w.lower() for w in concept.split() if len(w) > 3]
            match_count = sum(1 for w in concept_words if w in resp_lower)
            if match_count < max(1, len(concept_words) // 2):
                failures.append(f"Missing expected concept: '{concept}'")

        # 4. must_refuse_to_disclose
        for item in expect.get("must_refuse_to_disclose", []):
            if not any(k in resp_lower for k in ["cannot", "refuse", "not disclose", "restricted", "privacy", "security"]):
                failures.append(f"Did not refuse to disclose: '{item}'")

        # 5. must_ask_for
        for item in expect.get("must_ask_for", []):
            if item.lower() not in resp_lower and "order id" not in resp_lower:
                failures.append(f"Did not ask for required item: '{item}'")

        # 6. required_sources
        for src in expect.get("required_sources", []):
            if src not in sources and src not in resp_text:
                failures.append(f"Missing required source citation: '{src}'")

        # 7. forbidden_sources_as_authority
        for fsrc in expect.get("forbidden_sources_as_authority", []):
            if fsrc in sources:
                failures.append(f"Forbidden source used as authority: '{fsrc}'")

        # 8. tool expectation
        expected_tool = expect.get("tool")
        if expected_tool == "not_called":
            if tool_called is not None:
                failures.append(f"Tool was called ({tool_called}) when expected not_called")
        elif expected_tool == "not_called_without_id":
            if tool_called is not None:
                failures.append(f"Tool was called ({tool_called}) without an order ID")
        elif expected_tool == "order_lookup":
            if tool_called != "order_lookup":
                failures.append(f"Expected order_lookup tool call, got: {tool_called}")

        # 9. tool_arguments
        expected_args = expect.get("tool_arguments")
        if expected_args:
            for k, v in expected_args.items():
                if tool_args.get(k) != v:
                    failures.append(f"Tool arg mismatch for '{k}': expected '{v}', got '{tool_args.get(k)}'")

        # 10. handoff
        expected_handoff = expect.get("handoff")
        if expected_handoff is not None and expected_handoff != handoff:
            failures.append(f"Handoff mismatch: expected {expected_handoff}, got {handoff}")

        # 11. must_not_silently_choose_one (Source Conflict)
        if expect.get("must_not_silently_choose_one"):
            if "conflict" not in resp_lower and "inconsistent" not in resp_lower:
                failures.append("Failed to acknowledge source conflict.")

        passed = len(failures) == 0
        return passed, failures

    def run_all(self, test_files: List[Path]) -> bool:
        all_passed = True
        total_count = 0
        passed_count = 0
        category_stats: Dict[str, Dict[str, int]] = {}

        print("=" * 80)
        print("  Aster & Row Support Agent - Automated Evaluation Suite")
        print(f"  Active Provider: {self.agent.provider.upper()}")
        print("=" * 80)

        for filepath in test_files:
            if not filepath.exists():
                print(f"[!] Warning: Evaluation file not found: {filepath}")
                continue

            print(f"\n>> Running suite from: {filepath.name}")
            with open(filepath, "r", encoding="utf-8") as f:
                suite = json.load(f)

            for case in suite.get("cases", []):
                total_count += 1
                case_id = case.get("id", f"case_{total_count}")
                category = case.get("category", "general")

                if category not in category_stats:
                    category_stats[category] = {"total": 0, "passed": 0}
                category_stats[category]["total"] += 1

                passed, failures = self.run_case(case)

                if passed:
                    passed_count += 1
                    category_stats[category]["passed"] += 1
                    print(f"  [PASS] {case_id:<35} (Category: {category})")
                else:
                    all_passed = False
                    print(f"  [FAIL] {case_id:<35} (Category: {category})")
                    for err in failures:
                        print(f"         * {err}")

        # Print Category Summary Table
        print("\n" + "=" * 80)
        print("  EVALUATION SUMMARY BY CATEGORY")
        print("=" * 80)
        print(f"  {'Category':<30} | {'Passed':<8} | {'Total':<8} | {'Pass Rate':<10}")
        print("  " + "-" * 62)
        for cat, stats in sorted(category_stats.items()):
            rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"  {cat:<30} | {stats['passed']:<8} | {stats['total']:<8} | {rate:>6.1f}%")
        print("  " + "-" * 62)
        total_rate = (passed_count / total_count) * 100 if total_count > 0 else 0
        print(f"  {'OVERALL':<30} | {passed_count:<8} | {total_count:<8} | {total_rate:>6.1f}%")
        print("=" * 80)

        return all_passed

def main():
    runner = EvaluationRunner()
    visible_file = BASE_DIR / "evaluation" / "visible-cases.json"
    custom_file = BASE_DIR / "evaluation" / "custom-cases.json"
    success = runner.run_all([visible_file, custom_file])
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
