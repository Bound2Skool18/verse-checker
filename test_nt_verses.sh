#!/bin/bash
# Test New Testament verses once upload is complete

echo "🧪 Testing New Testament Bible Verse API"
echo "========================================"

BASE_URL="https://verse-checker.onrender.com"

# Test 1: Famous John verse
echo "📖 Test 1: John 3:16 (For God so loved the world)"
curl -X POST "$BASE_URL/check" \
  -H "Content-Type: application/json" \
  -d '{"quote": "For God so loved the world that he gave his one and only Son"}' \
  | grep -o '"score":[0-9.]*\|"reference":"[^"]*"\|"match":[a-z]*' || echo "No response"

echo -e "\n"

# Test 2: Love your neighbor
echo "📖 Test 2: Matthew 22:39 (Love your neighbor)"  
curl -X POST "$BASE_URL/check" \
  -H "Content-Type: application/json" \
  -d '{"quote": "love your neighbor as yourself"}' \
  | grep -o '"score":[0-9.]*\|"reference":"[^"]*"\|"match":[a-z]*' || echo "No response"

echo -e "\n"

# Test 3: Faith Hope Love
echo "📖 Test 3: 1 Corinthians 13:13 (Faith, Hope, Love)"
curl -X POST "$BASE_URL/check" \
  -H "Content-Type: application/json" \
  -d '{"quote": "faith hope and love these three remain but the greatest is love"}' \
  | grep -o '"score":[0-9.]*\|"reference":"[^"]*"\|"match":[a-z]*' || echo "No response"

echo -e "\n"

# Test 4: I am the way
echo "📖 Test 4: John 14:6 (I am the way)"
curl -X POST "$BASE_URL/check" \
  -H "Content-Type: application/json" \
  -d '{"quote": "I am the way the truth and the life"}' \
  | grep -o '"score":[0-9.]*\|"reference":"[^"]*"\|"match":[a-z]*' || echo "No response"

echo -e "\n"

# Test 5: Philippians joy
echo "📖 Test 5: Philippians 4:4 (Rejoice in the Lord)"
curl -X POST "$BASE_URL/check" \
  -H "Content-Type: application/json" \
  -d '{"quote": "rejoice in the Lord always again I say rejoice"}' \
  | grep -o '"score":[0-9.]*\|"reference":"[^"]*"\|"match":[a-z]*' || echo "No response"

echo -e "\n"

echo "🎯 If these tests return high similarity scores (>0.7) and correct references,"
echo "   your New Testament verses are successfully uploaded!"
echo ""
echo "📊 To check current upload progress:"  
echo "   python3 check_progress.py"