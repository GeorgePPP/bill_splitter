# Session Management Setup Guide

This document explains how to set up and use the session management feature in the Bill Splitter application.

## Overview

The session management feature allows users to:
- Automatically save their progress as they use the app
- Restore their previous session when they return
- Continue where they left off without losing data
- **Preserve participants across multiple bills** - users who were added in previous sessions are remembered
- **Quick-add known participants** - easily add people you've used before
- **Smart bill splitting** - start new bills with the same people or new people
- Handle multiple concurrent sessions

## Database Schema

The session management uses two tables in Supabase:

### sessions table
- `id`: UUID primary key
- `session_token`: Unique session identifier
- `user_id`: Optional user reference (for future auth integration)
- `expires_at`: Session expiration timestamp
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### bill_sessions table
- `id`: UUID primary key
- `session_token`: Foreign key to sessions table
- `current_step`: Current step in the bill splitting process (1-4)
- `participants`: JSON array of participants
- `receipt_data`: JSON object containing receipt data
- `receipt_id`: Reference to uploaded receipt
- `item_assignments`: JSON array of item assignments
- `split_results`: JSON object containing split calculations
- `known_participants`: JSON array of all participants ever added to this session
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Environment Variables

Add these variables to your backend `.env` file:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Backend Implementation

### SessionService
- Handles all database operations for sessions
- Manages session creation, retrieval, updates, and cleanup
- Implements session expiry logic (5 minutes with activity-based extension)

### API Endpoints
- `POST /api/session/create` - Create new session
- `GET /api/session/{token}` - Get session data
- `PUT /api/session/{token}` - Update session data
- `DELETE /api/session/{token}` - Delete session

## Frontend Implementation

### useSession Hook
- Manages session state and operations
- Handles automatic session initialization
- Provides methods for saving different types of data
- Manages session restoration logic

### Integration with Existing Hooks
- `useBillSplitter` - Auto-saves step changes, participants, receipt data, and split results
- `useItemAssignment` - Auto-saves item assignments as they're made

### User Experience
1. When a user first visits the app, a new session is created automatically
2. As the user progresses, their data is saved automatically
3. If the user returns and has an existing session, it automatically restores their progress
4. Sessions expire after 5 minutes of inactivity, but extend automatically with each action
5. Users can choose to add previously used participants or start fresh naturally through the UI

## Usage

The session management works automatically with minimal code changes:

1. The `useSession` hook is initialized in `App.tsx`
2. Other hooks receive session actions as parameters
3. Data is automatically saved when state changes occur
4. Session restoration happens on app initialization

## Participant Management Features

### Known Participants
- Every participant added to a session is stored in the `known_participants` array
- This creates a persistent "address book" of people within each session
- Known participants persist across multiple bills within the same session

### Quick Add Interface
- The ParticipantManager component displays previously added people
- Users can click on any known participant to quickly add them to the current bill
- Only participants not already in the current list are shown as options

### Smart Bill Starting
After completing a bill split, users have three options:
1. **"Split Another Bill (Same People)"** - Starts a new bill with the same participants
2. **"Split Another Bill (New People)"** - Starts a new bill with no participants
3. **"Start Completely Over"** - Creates a brand new session (loses all history)

### API Endpoints for Participant Management
- `POST /api/session/{token}/add-participants` - Add participants to known list
- `POST /api/session/{token}/new-bill` - Start new bill with optional participant preservation

## Key Features

- **Automatic Persistence**: No manual save actions required
- **Session Restoration**: Smart detection of existing sessions
- **Participant Memory**: Remembers all participants across different bills
- **Quick Add**: One-click adding of previously used participants
- **Smart Bill Options**: Choose to keep same people or start with new people
- **Smart Expiry**: 5-minute timeout with automatic extension on activity
- **Error Handling**: Robust error handling for network issues
- **Guest Sessions**: No authentication required, works for anonymous users

## Future Enhancements

- User authentication integration
- Session sharing between devices
- Session history and multiple saved sessions
- Advanced session management (rename, delete specific sessions)
