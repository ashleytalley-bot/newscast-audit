from docs.lib.cleaners import normalize_newscast
import re

print("Testing 5:30PM normalization...")

# Exact string from user report could be "5:30PM." or "5:30PM" or "5:30 PM"
test_inputs = [
    "5:30PM.",
    "5:30PM",
    "5:30 PM",
    " 5:30PM. ",
    "5:30pm."
]

failed = False
for i in test_inputs:
    res = normalize_newscast(i)
    print(f"Input: '{i}' -> Output: '{res}'")
    if res != "5 pm":
        print("  FAILED! Expected '5 pm'")
        failed = True

if failed:
    print("\nFAIL: At least one case failed.")
    # Debug: showing compiled patterns to see what's wrong
    from docs.lib.cleaners import _NEWSCAST_PATTERNS
    print("\nChecking patterns for 5:30:")
    for pat, out, desc in _NEWSCAST_PATTERNS:
        if "5:30" in pat:
            print(f"  Pattern: {pat} -> {out}")
else:
    print("\nSUCCESS: All cases passed.")
