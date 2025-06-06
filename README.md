# Solana Transaction Tracker

Real-time Solana wallet transaction monitoring and analysis tool with detailed inspection of smart contract interactions, token transfers, and program invocations.

## Features
- Real-time transaction monitoring
- Detailed transaction analysis
- Token balance tracking
- Smart contract interaction detection
- Bot activity warnings
- Support for various Solana programs (Jupiter, Raydium, Orca, etc.)

## Detailed Features

### Transaction Monitoring
- Real-time tracking of wallet activities
- Automatic detection of bot-like behaviors
- Detailed transaction breakdowns
- Smart contract interaction analysis

### Supported Programs & Operations
- Jupiter Aggregator (Swaps)
- Raydium/Orca/Serum DEX interactions
- Metaplex NFT operations
- Token transfers and approvals
- System program transactions
- Memo program messages

### Analytics & Detection
- Bot activity warnings (frequency analysis)
- Balance change tracking (SOL + SPL tokens)
- Fee payments monitoring
- Program interaction patterns

## Installation
```bash
git clone https://github.com/yourusername/solana-tx-tracker.git
cd solana-tx-tracker
pip install -r requirements.txt
```

## Configuration
1. Get your Helius API key from https://helius.xyz/
2. Replace the API key in `constants.py`:
```python
HELIUS_RPC = "https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY"
HELIOUS_WS = "wss://rpc.helius.xyz/?api-key=YOUR_API_KEY"
```

## Usage
```bash
python main.py
```
Then enter the Solana wallet address you want to monitor.

## User Manual

### Basic Usage
1. Start the program:
```bash
python main.py
```

2. Enter a Solana wallet address when prompted:
```
Nhập địa chỉ ví Solana cần theo dõi: <wallet_address>
```

3. Initial analysis will show:
- Current SOL balance
- Token holdings
- Recent transactions

4. Real-time monitoring will begin automatically:
- Transaction notifications
- Detailed breakdowns
- Balance changes
- Program interactions

### Understanding Output

#### Transaction Header
```
CHI TIẾT GIAO DỊCH MỚI
------------------------
TxHash       : <hash>
Slot         : <slot_number>
Block Time   : <timestamp>
Status       : Thành công/Thất bại
Phí          : <fee> SOL
```

#### Program Interactions
- System Program: SOL transfers
- Token Program: SPL token operations
- Jupiter: Token swaps
- Raydium/Orca: DEX operations

#### Warning Indicators
- 🟡 Normal activity
- 🟠 High frequency (possible bot)
- 🔴 Very high frequency (likely bot)

### Keyboard Controls
- `Ctrl+C`: Exit program
- Program auto-reconnects on connection loss
- Auto-retries on API failures

### Troubleshooting

#### Common Issues
1. **Connection Errors**
   - Check internet connection
   - Verify API key validity
   - Ensure wallet address is correct

2. **Missing Data**
   - Transaction may be too recent
   - RPC node might be syncing
   - Try alternative RPC endpoint

3. **Performance Issues**
   - High transaction volume wallet
   - Network congestion
   - Limited API rate

## Project Structure
```
solana-tx-tracker/
├── main.py              # Entry point
├── constants.py         # Configuration and constants
├── utils.py            # Utility functions
├── solana_client.py    # Solana RPC client
└── transaction_monitor.py # Transaction monitoring logic
```

## Requirements
- Python 3.7+
- websockets
- requests
- base58

## License
MIT License

## Author
Chau Huynh Phuc (Cyhapun)
