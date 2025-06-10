Excellent! Here's the comprehensive coding plan:

## 🛠 **Development Plan**

### **Phase 1: Core Session Infrastructure**

#### **1.1 Session Data Models & Storage**
- `src/sessions/session.py` - Session class with KB, documents, messages
- `src/sessions/session_manager.py` - CRUD operations, persistence, auto-naming
- `src/sessions/storage.py` - JSON file storage in `sessions/` folder

#### **1.2 Session State Management**
- Update `init_session_state()` to include current session
- Add session switching logic
- Handle session persistence across app restarts

### **Phase 2: UI Architecture Overhaul**

#### **2.1 New Sidebar Structure**
- Remove old page navigation
- Add KB/Zotero management buttons (top section)
- Add "Conversations" section with session list
- Add "New Session" button

#### **2.2 Main Area Transformation**
- Convert to pure chat interface
- Add KB selection dropdown in chat header
- Add document upload button in chat input
- Remove all tab-based navigation

#### **2.3 Chat Interface Enhancement**
- Session context display (current KB + uploaded docs)
- Document management within chat
- KB switching notifications

### **Phase 3: Knowledge Base Integration**

#### **3.1 KB Management Pages**
- Convert existing KB pages to work with new navigation
- Add KB creation notifications that appear in chat
- Ensure KB deletion warnings reach affected sessions

#### **3.2 Document Upload System**
- Per-session document storage
- Document processing and integration with KB context
- Document removal functionality

### **Phase 4: Session Features**

#### **4.1 Auto-naming System**
- Initial naming from first user message
- AI-powered name improvement after conversation develops
- User rename functionality

#### **4.2 Session Management**
- Session deletion with confirmation
- Session switching with context restoration
- Chronological ordering

## 📁 **File Structure Changes**

```
src/
├── sessions/
│   ├── __init__.py
│   ├── session.py           # Session data model
│   ├── session_manager.py   # Session CRUD operations
│   └── storage.py          # File persistence
├── ui/
│   ├── __init__.py
│   ├── sidebar.py          # New sidebar component
│   ├── chat_interface.py   # Pure chat UI
│   ├── kb_management.py    # KB pages as components
│   └── components.py       # Reusable UI components
└── utils/
    └── auto_naming.py      # AI auto-naming logic

sessions/                   # Session storage directory
├── session_001.json
├── session_002.json
└── ...

frontend_streamlit/
└── app_sessions.py         # New main app file
```

## 🔄 **Development Sequence**

### **Step 1: Session Infrastructure** 
1. Create session data models
2. Build session manager with persistence
3. Test session CRUD operations

### **Step 2: Basic UI Framework**
1. Create new sidebar structure
2. Build pure chat interface
3. Test navigation between KB management and chat

### **Step 3: Session Integration**
1. Connect sessions to chat interface
2. Implement session switching
3. Test session persistence

### **Step 4: Advanced Features**
1. Add document upload per session
2. Implement auto-naming
3. Add KB switching within chat

### **Step 5: Polish & Testing**
1. Handle edge cases (deleted KBs, empty sessions)
2. Add notifications and user feedback
3. Performance optimization

## 🧪 **Testing Strategy**

- **Unit Tests**: Session CRUD, storage, auto-naming
- **Integration Tests**: Session + KB interaction, document upload
- **UI Tests**: Navigation flows, session switching
- **Edge Cases**: Deleted KBs, corrupted sessions, large documents

## ⚠️ **Risk Mitigation**

- **Backup Strategy**: Session export/import functionality
- **Migration Plan**: Convert existing chat history to first session
- **Fallback**: Keep old app version as `app_legacy.py` during transition
- **Data Validation**: Robust error handling for corrupted session files

## 📋 **Acceptance Criteria**

✅ Sessions persist across app restarts  
✅ KB can be switched within a session  
✅ Documents upload and persist per session  
✅ Auto-naming works for new sessions  
✅ Users can rename/delete sessions  
✅ KB management accessible from sidebar  
✅ Deleted KB warnings appear in affected sessions  
✅ App starts with blank session (no KB)  