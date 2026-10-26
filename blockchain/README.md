# AEGIS Blockchain - Private Network

A fully offline private blockchain network for AEGIS IoT platform, enabling multiple customers to request requirements and manually accept/reject them through immutable audit trails.

## Quick Start

### 1. Start Private Network
```bash
cd blockchain
npm run start:private
```
This starts a local Hardhat network simulating your private blockchain.

### 2. Deploy Contract
```bash
npm run deploy
```
Deploys the AegisAudit contract to your private network.

### 3. Run Multi-Customer Demo
```bash
npm run demo:multi-customer
```
Shows how multiple customers can request requirements and others can approve/reject them.

### 4. Test Individual Features
```bash
npm run demo:single
```
Tests all contract functionality with detailed logging.

## Network Configuration

- **Chain ID**: 31337 (Hardhat), 12345 (Private)
- **Accounts**: 10 pre-funded test accounts
- **Gas**: Unlimited (for testing)
- **Mining**: Automatic (new blocks every 3 seconds)

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run start:private` | Start private blockchain network |
| `npm run deploy` | Deploy to localhost network |
| `npm run deploy:private` | Deploy to configured private network |
| `npm run demo:multi-customer` | Run requirement request/approval demo |
| `npm run demo:single` | Run comprehensive contract testing |
| `npm run test` | Run unit tests |
| `npm run coverage` | Generate test coverage report |
| `npm run compile` | Compile smart contracts |

## Contract Features

### For Your Use Case
- ✅ **Multi-customer support**: 10+ customers can participate
- ✅ **Requirement requests**: Customers can submit requirements
- ✅ **Manual approval/rejection**: Any customer can accept or reject requests
- ✅ **Emergency handling**: Critical requests with priority processing
- ✅ **Audit trails**: Immutable logs of all interactions
- ✅ **Real-time notifications**: Event subscription system
- ✅ **Privacy**: Completely offline, no public exposure

### Technical Features
- **Severity levels**: INFO, WARNING, ERROR, CRITICAL
- **Batch operations**: Process multiple logs efficiently
- **Compliance reporting**: Generate audit summaries
- **Event subscriptions**: Real-time requirement updates
- **Multi-tenant**: Isolated customer data spaces

## Private Network Setup

### For Production Use
1. **Multiple Nodes**: Each customer runs their own blockchain node
2. **Private Connectivity**: VPN or dedicated network links
3. **Custom Chain ID**: Use 12345 or your own chain ID
4. **Access Control**: Only authorized customers can join

### Configuration
Update `hardhat.config.js` networks.private with your network details:
```javascript
private: {
  url: "http://your-private-node:8545",
  accounts: [process.env.PRIVATE_KEY],
  chainId: 12345,
}
```

## Integration

### Backend API
- REST endpoints for requirement submission
- WebSocket connections for real-time updates
- Database sync with blockchain state

### Frontend
- Requirement submission forms
- Approval/rejection interfaces
- Live notification system
- Analytics dashboard

### IoT Sensors
- Blockchain-verified sensor data
- Automated requirement generation
- Maintenance scheduling

## Security

- **Offline operation**: No internet connectivity required
- **Permissioned access**: Only authorized customers
- **Immutable audit trails**: All actions permanently recorded
- **Data privacy**: Requirements stay within private network

## Demo Output

The multi-customer demo shows:
- Customer 1 requests sensor installation
- Customer 2 approves the request
- Customer 3 requests maintenance
- Customer 4 rejects the maintenance
- Customer 5 makes emergency request
- Customer 1 approves emergency access

All interactions are logged immutably with full audit trails.

## Next Steps

1. **Customize contract events** for your specific requirement types
2. **Add business logic** for automated approvals if needed
3. **Set up multiple physical nodes** for production network
4. **Integrate with AEGIS backend** for seamless operation
5. **Implement frontend interfaces** for customer interactions

This private blockchain provides the foundation for your secure, transparent requirement management system.

```
PRIVATE_KEY=0x...          # Your deployment private key
SEPOLIA_RPC_URL=...        # Sepolia testnet RPC
ETHERSCAN_API_KEY=...      # For contract verification
REPORT_GAS=false           # Set to true for gas reports
```

**⚠️ Never commit `.env` to version control!**

## Local Development

### Start Local Hardhat Network

```bash
npm run node
```

This starts a local Ethereum network at `http://localhost:8545`.

### Compile Contracts

```bash
npm run compile
```

Compiles Solidity contracts to the `artifacts/` directory.

### Run Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run with coverage report
npm run coverage

# Generate gas report
npm run gas-report
```

## Deployment

### Local Network

For one-command startup from the repository root, run:

```powershell
.\start_blockchain.bat
```

The script starts Anvil with a local state file when Anvil is installed, checks the
chain ID and existing contract deployment, deploys only when the saved address has
no contract code, runs contract setup, and starts the backend if it is not already
running. Keep the node window open while using Aegis. The state file is stored in
`blockchain/.local-state/` and is ignored by Git.

If Anvil is unavailable, the script falls back to the Hardhat node so the demo can
still run, but Hardhat's default node is in-memory and loses chain history when it
exits. In that fallback mode, a new deployment is required after each node restart.

Manual Hardhat startup (non-persistent development chain):

1. Start Hardhat node (terminal 1):
```bash
npm run node
```

2. Deploy contract (terminal 2):
```bash
npm run deploy
```

This deploys to `localhost` and saves deployment info to `deployments/localhost-deployment.json`.

### Setup Contract

After deployment, initialize authorized loggers:

```bash
npx hardhat run scripts/setup.js --network localhost
```

### Sepolia Testnet

1. Get Sepolia ETH from a faucet:
   - https://sepoliafaucet.com/

2. Deploy to Sepolia:
```bash
npm run deploy:sepolia
```

### Verify on Etherscan

After deploying to Sepolia:

```bash
npm run verify -- 0xCONTRACT_ADDRESS
```

## Smart Contract: AegisAudit

### Overview

The `AegisAudit` contract provides immutable audit logging with:
- Tenant isolation (multi-tenant support)
- Role-based access control
- Cryptographic hash verification
- Event emission for indexing
- Efficient querying by tenant

### Key Features

#### 1. Log Creation

```solidity
function createLog(
    string memory _eventType,
    bytes32 _dataHash,
    string memory _metadata,
    uint256 _tenantId
) external onlyAuthorized returns (bytes32)
```

Creates an immutable audit log entry.

**Parameters:**
- `_eventType`: Type of event (e.g., "DEVICE_ACTIVATED")
- `_dataHash`: Keccak256 hash of event data
- `_metadata`: JSON metadata as string
- `_tenantId`: Tenant ID for isolation

**Returns:** Log ID (bytes32)

#### 2. Access Control

Owner can manage authorized loggers:

```solidity
function addAuthorizedLogger(address _account) external onlyOwner
function removeAuthorizedLogger(address _account) external onlyOwner
```

#### 3. Log Verification

Verify log integrity:

```solidity
function verifyLog(
    bytes32 _logId,
    bytes32 _expectedHash
) external returns (bool)
```

#### 4. Querying

Get logs by tenant:

```solidity
function getTenantLogs(uint256 _tenantId) external view returns (bytes32[])
function getTenantLogCount(uint256 _tenantId) external view returns (uint256)
```

Get all logs:

```solidity
function getLogCount() external view returns (uint256)
function getAllLogs() external view returns (bytes32[])
```

### Events

The contract emits events for indexing:

- `LogCreated(bytes32 logId, uint256 tenantId, address actor, string eventType, uint256 timestamp)`
- `LogVerified(bytes32 logId, bool isValid)`
- `AuthorizerAdded(address account)`
- `AuthorizerRemoved(address account)`

## Testing

### Test Coverage

Tests cover:
- Contract deployment and initialization
- Log creation with various scenarios
- Access control enforcement
- Log querying (by tenant, all logs)
- Log verification (integrity checking)
- Ownership transfer
- Error cases and edge conditions

### Running Specific Tests

```bash
npx hardhat test --grep "Log Creation"
```

### Gas Analysis

Track gas usage with:

```bash
npm run gas-report
```

Gas optimization targets:
- Log creation: < 150,000 gas
- Log verification: < 50,000 gas
- Query operations: < 30,000 gas

## Integration with Backend

### Contract ABI

The contract ABI is automatically generated in:
```
artifacts/contracts/AegisAudit.sol/AegisAudit.json
```

Use this ABI with Web3.py for backend integration. Reading contract state only
requires the RPC endpoint, deployed contract address, and ABI; it does not
require a private key.

### Web3.py Integration Example

```python
from web3 import Web3
import json
from pathlib import Path

# Run from the blockchain directory after starting the same persistent node
# that contains the deployment.
with open('artifacts/contracts/AegisAudit.sol/AegisAudit.json', encoding='utf-8') as f:
    abi = json.load(f)['abi']

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
if not w3.is_connected():
    raise ConnectionError('Could not connect to the local blockchain RPC')

deployment = json.loads(Path('deployments/localhost-deployment.json').read_text(encoding='utf-8'))
address = Web3.to_checksum_address(deployment['AegisAudit'])
if not w3.eth.get_code(address):
    raise RuntimeError('No contract at this address on this chain; check the RPC and deployment')

contract = w3.eth.contract(address=address, abi=abi)
print('Chain ID:', w3.eth.chain_id)
print('Block:', w3.eth.block_number)
print('All contract logs:', contract.functions.getLogCount().call())
print('Tenant 1 compliance:', contract.functions.getComplianceSummary(1).call())

for log_id in contract.functions.getTenantLogs(1).call():
    print(contract.functions.getLog(log_id).call())
```

The backend uses `BLOCKCHAIN_RPC_URL` (default `http://127.0.0.1:8545`) and
`CONTRACT_ADDRESS`; when the latter is unset, it reads the address from
`deployments/localhost-deployment.json`. If a local node is restarted with a
fresh in-memory chain, the saved address may no longer contain a contract and
the old logs cannot be fetched from that reset chain. For writes, the backend
uses an RPC-unlocked account only when connected to loopback chain ID 31337;
other networks require `BLOCKCHAIN_PRIVATE_KEY`.

## Troubleshooting

### "Insufficient funds" error

Solution: Use accounts from Hardhat's default mnemonic or request testnet ETH.

### Contract compilation fails

```bash
npm run compile
```

Check Solidity syntax and version compatibility.

### Tests timeout

Increase timeout in `hardhat.config.js`:
```javascript
mocha: {
  timeout: 60000,  // 60 seconds
}
```

### Cannot connect to local network

Ensure Hardhat node is running:
```bash
npm run node
```

Verify it's accessible at `http://localhost:8545`.

## Security Considerations

1. **Private Key Protection**: Never commit private keys to git
2. **Access Control**: Only authorized addresses can create logs
3. **Immutability**: Logs cannot be modified or deleted
4. **Tenant Isolation**: Logs are segregated by tenant ID
5. **Hash Verification**: Logs can be verified for tampering

## Performance

### Gas Costs (Estimated)

- Create Log: ~120,000 gas
- Verify Log: ~25,000 gas
- Get Tenant Logs: ~5,000 gas (for small arrays)
- Get Log Count: ~2,000 gas

### Scalability

- Supports unlimited log entries
- Efficient querying by tenant ID
- Batch operations recommended for high volume

## References

- [Hardhat Documentation](https://hardhat.org/)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Ethereum Development](https://ethereum.org/developers/)

## Support

For issues or questions:
1. Check test files for examples
2. Review Solidity code comments
3. Consult Hardhat documentation

## Version History

- v1.0 - Initial release (May 2026)
  - Basic audit logging contract
  - Multi-tenant support
  - Role-based access control
  - Comprehensive test suite

---

**Last Updated:** May 2, 2026  
**Maintained by:** AEGIS Development Team
