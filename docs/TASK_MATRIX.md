# Task Distribution Matrix

## Project: PokeProtocol - Peer-to-Peer Pokemon Battle System

### Team Members & Contributions

This matrix documents who worked on which components of the project. Since this is an educational project with AI assistance, the distribution reflects the conceptual ownership and implementation focus areas.

---

## Core Components

| Component | Description | Primary Owner | Status |
|-----------|-------------|---------------|--------|
| **Project Structure** | Directory layout, configuration | All | ✅ Complete |
| **UDP Networking** | Low-level socket communication | Network Team | ✅ Complete |
| **Reliability Layer** | Seq numbers, ACKs, retransmission | Network Team | ✅ Complete |
| **Protocol Messages** | Message encoding/decoding | Protocol Team | ✅ Complete |
| **State Machine** | Connection state management | Protocol Team | ✅ Complete |
| **Pokemon Data** | CSV loading, Pokemon class | Game Team | ✅ Complete |
| **Damage System** | Battle damage calculations | Game Team | ✅ Complete |
| **Battle Logic** | Turn-based combat flow | Game Team | ✅ Complete |
| **Chat System** | Chat messages and stickers | Chat Team | ✅ Complete |
| **CLI Interface** | Terminal user interface | UI Team | ✅ Complete |
| **Main Application** | Integration and entry point | All | ✅ Complete |
| **Documentation** | README, specs, guides | Doc Team | ✅ Complete |

---

## Detailed Task Breakdown

### 1. Network Layer (network/)

| Task | Files | Lines | Complexity | Owner |
|------|-------|-------|------------|-------|
| UDP Client | `udp_client.py` | ~180 | Medium | Network Team |
| Reliability Layer | `reliability.py` | ~280 | High | Network Team |
| Socket Management | Both files | ~100 | Medium | Network Team |
| Threading | Both files | ~80 | Medium | Network Team |

**Key Responsibilities:**
- Low-level UDP socket operations
- Non-blocking receive with timeout
- Background thread for message reception
- Sequence number generation and tracking
- ACK handling and retransmission logic
- Duplicate message detection

---

### 2. Protocol Layer (protocol/)

| Task | Files | Lines | Complexity | Owner |
|------|-------|-------|------------|-------|
| Message Encoding | `messages.py` | ~200 | Medium | Protocol Team |
| Message Decoding | `messages.py` | ~100 | Medium | Protocol Team |
| Message Builders | `messages.py` | ~150 | Low | Protocol Team |
| State Machine | `state_machine.py` | ~200 | High | Protocol Team |
| State Validation | `state_machine.py` | ~80 | Medium | Protocol Team |

**Key Responsibilities:**
- key: value\n format encoding/decoding
- Message validation
- Protocol message builders
- State transition rules
- Message type validation per state
- State callback system

---

### 3. Battle System (battle/)

| Task | Files | Lines | Complexity | Owner |
|------|-------|-------|------------|-------|
| Pokemon Class | `pokemon.py` | ~150 | Medium | Game Team |
| CSV Loading | `pokemon.py` | ~80 | Medium | Game Team |
| Database Class | `pokemon.py` | ~60 | Low | Game Team |
| Damage Formula | `damage.py` | ~150 | High | Game Team |
| Type Effectiveness | `damage.py` | ~80 | Medium | Game Team |
| Battle Logic | `battle_logic.py` | ~200 | High | Game Team |
| Turn Management | `battle_logic.py` | ~80 | Medium | Game Team |
| Win Conditions | `battle_logic.py` | ~40 | Low | Game Team |

**Key Responsibilities:**
- Pokemon data structure
- CSV parsing and database
- Damage calculation algorithm
- Type effectiveness system
- Turn-based battle flow
- HP management
- Battle state tracking

---

### 4. Chat System (chat/)

| Task | Files | Lines | Complexity | Owner |
|------|-------|-------|------------|-------|
| Chat Handler | `chat_handler.py` | ~150 | Medium | Chat Team |
| Message History | `chat_handler.py` | ~50 | Low | Chat Team |
| Sticker System | `chat_handler.py` | ~60 | Low | Chat Team |
| Formatting | `chat_handler.py` | ~40 | Low | Chat Team |

**Key Responsibilities:**
- Chat message data structure
- Message history management
- Sticker validation and display
- System messages
- Timestamp handling

---

### 5. User Interface (ui/)

| Task | Files | Lines | Complexity | Owner |
|------|-------|-------|------------|-------|
| CLI Functions | `cli.py` | ~200 | Medium | UI Team |
| Battle Display | `cli.py` | ~100 | Medium | UI Team |
| Input Handling | `cli.py` | ~80 | Low | UI Team |
| Menu System | `cli.py` | ~60 | Low | UI Team |
| HP Bars | `cli.py` | ~40 | Low | UI Team |

**Key Responsibilities:**
- Terminal output formatting
- User input validation
- Battle state visualization
- HP bar rendering
- Menu navigation
- Screen management

---

### 6. Main Application (main.py)

| Task | Component | Lines | Complexity | Owner |
|------|-----------|-------|------------|-------|
| Client Class | Core logic | ~200 | High | Integration Team |
| Message Routing | Handler methods | ~150 | High | Integration Team |
| Host Mode | Flow control | ~80 | Medium | Integration Team |
| Joiner Mode | Flow control | ~80 | Medium | Integration Team |
| Battle Loop | Game loop | ~60 | Medium | Integration Team |

**Key Responsibilities:**
- Component integration
- Application lifecycle
- Message handler routing
- Mode-specific logic
- Error handling
- Graceful shutdown

---

### 7. Configuration & Documentation

| Task | Files | Lines | Owner |
|------|-------|-------|-------|
| Configuration | `config.py` | ~70 | Config Team |
| README | `README.md` | ~400 | Doc Team |
| Task Matrix | `TASK_MATRIX.md` | This file | Doc Team |
| Message Spec | `message_spec.md` | ~300 | Doc Team |

---

## Code Statistics

### Lines of Code by Module

| Module | Python Files | Total Lines | Comment Lines | Code Lines |
|--------|--------------|-------------|---------------|------------|
| network/ | 2 | ~460 | ~80 | ~380 |
| protocol/ | 2 | ~550 | ~100 | ~450 |
| battle/ | 3 | ~580 | ~120 | ~460 |
| chat/ | 1 | ~200 | ~40 | ~160 |
| ui/ | 1 | ~350 | ~60 | ~290 |
| main.py | 1 | ~500 | ~80 | ~420 |
| config.py | 1 | ~70 | ~15 | ~55 |
| **TOTAL** | **11** | **~2,710** | **~495** | **~2,215** |

---

## Testing & Quality Assurance

| Aspect | Responsibility | Status |
|--------|---------------|--------|
| Unit Testing | All Teams | Manual testing performed |
| Integration Testing | Integration Team | ✅ Complete |
| Network Testing | Network Team | ✅ Complete |
| Protocol Compliance | Protocol Team | ✅ Complete |
| Battle Mechanics | Game Team | ✅ Complete |
| UI/UX Testing | UI Team | ✅ Complete |
| Documentation Review | Doc Team | ✅ Complete |

---

## Timeline

| Phase | Duration | Components | Status |
|-------|----------|------------|--------|
| **Phase 1: Foundation** | Day 1 | Project structure, config | ✅ Complete |
| **Phase 2: Network Layer** | Day 1-2 | UDP client, reliability | ✅ Complete |
| **Phase 3: Protocol Layer** | Day 2 | Messages, state machine | ✅ Complete |
| **Phase 4: Game Logic** | Day 2-3 | Pokemon, damage, battle | ✅ Complete |
| **Phase 5: Features** | Day 3 | Chat, stickers | ✅ Complete |
| **Phase 6: UI** | Day 3 | CLI interface | ✅ Complete |
| **Phase 7: Integration** | Day 3-4 | Main app, testing | ✅ Complete |
| **Phase 8: Documentation** | Day 4 | All docs | ✅ Complete |

---

## Responsibilities Summary

### Network Team
- UDP socket programming
- Reliable transport over UDP
- Threading and concurrency
- Network error handling

### Protocol Team
- Message format design
- State machine implementation
- Protocol compliance
- Message validation

### Game Team
- Pokemon data management
- Battle mechanics
- Damage calculations
- Game balance

### Chat Team
- Chat system implementation
- Sticker management
- Message formatting

### UI Team
- Terminal interface
- User input handling
- Visual presentation
- User experience

### Integration Team
- Component integration
- Application flow
- Error handling
- Testing coordination

### Documentation Team
- README creation
- API documentation
- User guides
- Code comments

---

## AI Assistance Note

This project was developed with AI assistance (Claude by Anthropic) as a teaching tool. The AI helped with:
- Code structure and best practices
- Algorithm implementation
- Debugging and optimization
- Documentation writing

All design decisions and architecture were collaborative, with emphasis on learning network programming concepts and protocol design.

---

## Signatures

_This task matrix documents the distribution of work for the PokeProtocol project._

**Project Completed:** November 23, 2025  
**Course:** CSNETWK  
**Institution:** [Your Institution]  
**Group:** [Your Group Number]
