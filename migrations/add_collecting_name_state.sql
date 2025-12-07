-- Add COLLECTING_NAME to ConversationState enum
-- This allows the bot to ask for customer's name after language selection

-- Add the new enum value
ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'collecting_name';

-- Verify the change
-- SELECT enum_range(NULL::conversationstate);
