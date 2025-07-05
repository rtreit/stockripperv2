"""Test ticker extraction logic from the Stock Research Agent"""
import re

def test_ticker_extraction():
    """Test the ticker extraction logic"""
    test_messages = [
        "Analyze stock IBM",
        "Please analyze IBM stock",
        "What's your analysis of TSLA?",
        "Give me a stock analysis for IBM",
        "analyze stock aapl"
    ]
    
    for text in test_messages:
        print(f"Testing: '{text}'")
        
        # Method 1: Regex for uppercase letters
        ticker_match = re.search(r'\b([A-Z]{1,5})\b', text.upper())
        if ticker_match:
            ticker1 = ticker_match.group(1)
            print(f"  Regex method: {ticker1}")
        else:
            print("  Regex method: No match")
        
        # Method 2: Word parsing
        words = text.split()
        ticker2 = None
        for i, word in enumerate(words):
            if word.lower() in ["analyze", "stock", "ticker"] and i + 1 < len(words):
                ticker2 = words[i + 1].upper()
                break
        
        if ticker2:
            print(f"  Word parsing: {ticker2}")
        else:
            print("  Word parsing: No match")
        
        print()

if __name__ == "__main__":
    test_ticker_extraction()

