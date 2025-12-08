"""Test enum conversion"""
import sys
sys.path.insert(0, 'backend')

from database import ConversationState

print("Testing enum conversion:")
print(f"1. START = {ConversationState.START}")
print(f"2. Value = {ConversationState.START.value}")
print(f"3. Type = {type(ConversationState.START)}")

# Test string conversion
try:
    state1 = ConversationState("START")
    print(f"4. ConversationState('START') = {state1} ✅")
except Exception as e:
    print(f"4. ConversationState('START') FAILED: {e} ❌")

try:
    state2 = ConversationState("COLLECTING_NAME")
    print(f"5. ConversationState('COLLECTING_NAME') = {state2} ✅")
except Exception as e:
    print(f"5. ConversationState('COLLECTING_NAME') FAILED: {e} ❌")

try:
    state3 = ConversationState("collecting_name".upper())
    print(f"6. ConversationState('collecting_name'.upper()) = {state3} ✅")
except Exception as e:
    print(f"6. ConversationState('collecting_name'.upper()) FAILED: {e} ❌")

# Test all enum values
print("\n7. All enum values:")
for state in ConversationState:
    print(f"   - {state.name} = '{state.value}'")
