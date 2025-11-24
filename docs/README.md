# PokeProtocol - Peer-to-Peer Pokemon Battle System

A fully functional peer-to-peer Pokemon battle system implemented over UDP with custom reliability layer, following the PokeProtocol specification.

## 🎮 Features

- **UDP-based P2P Battle System**: Direct peer-to-peer communication without central server
- **Custom Reliability Layer**: Sequence numbers, ACKs, and automatic retransmission over UDP
- **Turn-based Pokemon Combat**: Complete battle system with damage calculation
- **Chat & Stickers**: Real-time chat with emoji stickers during battles
- **Protocol Compliance**: Follows PokeProtocol RFC message format (key: value\n)
- **Interoperability**: Compatible with other groups' implementations

## 📁 Project Structure

```
pokeprotocol/
├── main.py                  # CLI entry point (host/joiner/spectator)
├── config.py                # Ports, timeouts, constants, flags
├── data/
│   └── pokemon.csv          # Pokemon stats database (448 Pokemon)
├── network/
│   ├── udp_client.py        # Low-level UDP send/receive
│   └── reliability.py       # Sequence numbers, ACKs, retransmission
├── protocol/
│   ├── messages.py          # Encode/decode key: value\n messages
│   └── state_machine.py     # Battle states + transitions
├── battle/
│   ├── pokemon.py           # Pokemon class + CSV loading
│   ├── damage.py            # Damage formula
│   └── battle_logic.py      # Turn handling and HP updates
├── chat/
│   └── chat_handler.py      # CHAT_MESSAGE text + sticker handling
├── ui/
│   └── cli.py               # Terminal UI
└── docs/
    ├── README.md            # This file
    ├── TASK_MATRIX.md       # Task distribution
    └── message_spec.md      # Message format summary
```

## 🚀 How to Run

### Prerequisites

- Python 3.8 or higher
- No external dependencies required (uses only standard library)

### Starting a Battle

#### As Host (Player 1):

```bash
python main.py
```

1. Enter your player name
2. Select "Host (create game)"
3. Enter port number (e.g., 5000)
4. Wait for opponent to connect
5. Select your Pokemon
6. Battle!

#### As Joiner (Player 2):

```bash
python main.py
```

1. Enter your player name
2. Select "Join (connect to game)"
3. Enter host IP address (e.g., 127.0.0.1 for local, or peer's IP)
4. Enter host port number (e.g., 5000)
5. Enter your local port (e.g., 5001)
6. Select your Pokemon
7. Battle!

### Testing Locally

Open two terminals:

**Terminal 1 (Host):**
```bash
cd pokeprotocol
python main.py
# Choose: Host, Port: 5000
```

**Terminal 2 (Joiner):**
```bash
cd pokeprotocol
python main.py
# Choose: Join, Host: 127.0.0.1, Port: 5000, Local Port: 5001
```

## 🎯 Battle Flow

1. **Connection Phase**
   - Exchange HELLO messages
   - Establish peer connection

2. **Pokemon Selection**
   - Each player selects from 6 random Pokemon
   - Exchange POKEMON_SELECT messages

3. **Ready Phase**
   - Both players signal READY
   - Host determines first player (based on speed)
   - Host sends BATTLE_START

4. **Battle Phase**
   - Turn-based combat
   - Players send ATTACK messages
   - Damage calculated and applied
   - HP updates exchanged

5. **End Phase**
   - Battle ends when Pokemon faints
   - BATTLE_RESULT message sent
   - Display winner

## 📨 Message Format

All messages follow the format:
```
type: <MESSAGE_TYPE>
key1: value1
key2: value2

```

Example ATTACK message:
```
type: ATTACK
seq: 42
attacker: Player1
move_type: fire
damage: 45
critical: true

```

See `docs/message_spec.md` for complete message specifications.

## 🛡️ Reliability Features

- **Sequence Numbers**: Every message has unique sequence number
- **Acknowledgments**: Recipient sends ACK for received messages
- **Retransmission**: Unacknowledged messages retransmitted after timeout
- **Duplicate Detection**: Sequence numbers prevent duplicate processing
- **Timeout Handling**: Configurable timeout and retry limits

## ⚔️ Battle Mechanics

### Damage Calculation

Simplified Pokemon formula:
```
Damage = ((2 * Level / 5 + 2) * Power * Attack / Defense / 50 + 2) * Modifiers
```

Where:
- Level = 50 (constant)
- Power = Move base power (50-60 depending on type)
- Attack/Defense = Pokemon stats (physical or special)
- Modifiers include:
  - STAB (Same Type Attack Bonus): 1.5x
  - Type effectiveness: 0x to 4x
  - Random factor: 0.85x to 1.0x
  - Critical hit: 2x damage (4.17% chance)

### Type Effectiveness

Uses actual Pokemon type chart from CSV data. Examples:
- Fire vs Grass = 2x (super effective)
- Water vs Fire = 2x (super effective)
- Fire vs Water = 0.5x (not very effective)
- Ghost vs Normal = 0x (no effect)

## 💬 Chat & Stickers

During battle, players can send chat messages and stickers:

**Available Stickers:**
1. 😀 Happy
2. 😢 Sad
3. 😠 Angry
4. 👍 Thumbs Up
5. ❤️ Heart
6. 🔥 Fire
7. ⚡ Thunder
8. 💧 Water
9. 🌿 Grass
10. 🎉 Party

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Network
DEFAULT_PORT = 5000
BUFFER_SIZE = 4096

# Reliability
ACK_TIMEOUT = 2.0        # seconds
MAX_RETRIES = 5

# Debug
DEBUG_MODE = False
VERBOSE_LOGGING = False
```

## 🐛 Troubleshooting

### Connection Issues

- **"Failed to bind port"**: Port already in use, try different port
- **"No response from peer"**: Check firewall settings, verify IP/port
- **"Connection timeout"**: Ensure both machines are on same network

### Battle Issues

- **"Not your turn"**: Wait for opponent to complete their turn
- **Pokemon not appearing**: Check that pokemon.csv is in data/ folder

### Debug Mode

Enable detailed logging in `config.py`:
```python
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

## 📊 Pokemon Database

Includes 448 Pokemon (Generations 1-4) with:
- Base stats (HP, Attack, Defense, Sp. Attack, Sp. Defense, Speed)
- Types (primary and secondary)
- Abilities
- Type effectiveness chart
- Physical attributes

## 🎓 Educational Value

This project demonstrates:
- **Network Programming**: UDP sockets, peer-to-peer architecture
- **Protocol Design**: Custom message format, state machines
- **Reliability**: Building reliable transport over unreliable protocol
- **Game Development**: Turn-based combat, game state management
- **Software Engineering**: Modular design, separation of concerns

## 📜 Credits

- Pokemon data: The Pokemon Company
- Protocol specification: PokeProtocol RFC
- Implementation: CSNETWK Group

## 🤖 AI Assistance Note

This project was developed with assistance from AI (Claude) as a learning tool for network programming concepts. All core logic, protocol implementation, and battle mechanics were designed and implemented through collaborative problem-solving.

## 📝 License

Educational project for CSNETWK course.
