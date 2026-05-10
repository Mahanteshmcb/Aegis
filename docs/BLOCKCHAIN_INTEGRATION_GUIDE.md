# AEGIS Backend-Blockchain Integration Guide

## Overview

This guide documents the integration between the AEGIS FastAPI backend and the private AegisAudit blockchain network. The integration enables immutable audit logging, compliance tracking, and requirement management through smart contracts.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │────│ Blockchain       │────│ AegisAudit      │
│   Backend       │    │ Connector        │    │ Smart Contract  │
│                 │    │ (Web3.py)        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────────────┐
                    │ Private Blockchain │
                    │ Network (Chain ID │
                    │ 12345)            │
                    └────────────────────┘
```

## Prerequisites

### Environment Variables

Set the following environment variables in your `.env` file:

```bash
# Blockchain Configuration
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0xYourDeployedContractAddress
BLOCKCHAIN_PRIVATE_KEY=0xyour_private_key_here
```

### Dependencies

Install required packages:

```bash
cd backend
pip install -r requirements.txt
```

Key dependencies:
- `web3==5.29.2`: Ethereum blockchain interaction
- `eth-account==0.5.9`: Transaction signing and account management

## Blockchain Connector

The `BlockchainConnector` class handles all blockchain interactions:

### Initialization

```python
from backend.blockchain_connector import get_blockchain_connector

# Get configured connector instance
blockchain = await get_blockchain_connector()
```

### Connection Management

```python
# Check connection status
status = await blockchain.get_network_info()
print(f"Connected: {blockchain.is_connected}")
print(f"Chain ID: {status['network_id']}")
print(f"Block Number: {status['block_number']}")
```

## API Endpoints

### Audit Logs from Blockchain

**GET** `/api/v1/audit/blockchain`

Retrieve audit logs directly from the blockchain:

```bash
# Get recent logs for current tenant
curl -H "Authorization: Bearer <token>" \
     http://localhost:8001/api/v1/audit/blockchain

# Filter by event type
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8001/api/v1/audit/blockchain?event_type=REQUIREMENT_REQUEST"

# Limit results
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8001/api/v1/audit/blockchain?limit=10"
```

### Submit Requirement Request

**POST** `/api/v1/audit/requirement/request`

Submit a new requirement to the blockchain:

```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "event_type=REQUIREMENT_REQUEST" \
     -d "data_hash=0x123..." \
     -d "metadata=New security requirement for zone access" \
     http://localhost:8001/api/v1/audit/requirement/request
```

### Approve/Reject Requirements

**POST** `/api/v1/audit/requirement/{log_id}/approve`

```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "approval_metadata=Approved by security team" \
     http://localhost:8001/api/v1/audit/requirement/0x123.../approve
```

**POST** `/api/v1/audit/requirement/{log_id}/reject`

```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "rejection_metadata=Insufficient evidence provided" \
     http://localhost:8001/api/v1/audit/requirement/0x123.../reject
```

### Compliance Reports

**GET** `/api/v1/audit/compliance/{tenant_id}`

Get compliance summary for a tenant:

```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8001/api/v1/audit/compliance/1
```

Response:
```json
{
  "tenant_id": 1,
  "compliance_summary": {
    "total_logs": 150,
    "verified_logs": 145,
    "critical_logs": 3,
    "emergency_logs": 0
  }
}
```

### System Statistics

**GET** `/api/v1/audit/statistics`

Get system-wide audit statistics:

```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8001/api/v1/audit/statistics
```

### Blockchain Status

**GET** `/api/v1/blockchain/status`

Check blockchain connection and network info:

```bash
curl http://localhost:8001/api/v1/blockchain/status
```

## Security Considerations

### Private Key Management

- **Never store private keys in code or version control**
- Use environment variables or secure key management services
- Rotate keys regularly
- Use dedicated blockchain accounts with minimal permissions

### Transaction Signing

- All blockchain transactions require private key signing
- Transactions are gas-efficient and include proper nonce management
- Failed transactions are logged but don't crash the API

### Access Control

- All blockchain endpoints require authentication
- Tenant isolation is enforced at the API level
- Admin users can access cross-tenant compliance data

### Network Security

- Private blockchain network (Chain ID: 12345)
- No external RPC exposure
- Local Hardhat network for development/testing

## Error Handling

The integration includes comprehensive error handling:

- **Connection failures**: Graceful fallback to database-only mode
- **Transaction failures**: Detailed error messages with transaction hashes
- **Contract errors**: Smart contract revert reasons are captured
- **Network timeouts**: Configurable timeouts with retry logic

## Monitoring

### Transaction Monitoring

Monitor blockchain transactions through:

1. **Transaction receipts**: All successful transactions return hashes
2. **Event logs**: Smart contract events are indexed and searchable
3. **Network status**: Real-time connection and sync status

### Health Checks

```python
# Check blockchain health
status = await blockchain.get_network_info()
if not status.get('is_syncing', True):  # Not syncing = healthy
    print("Blockchain network is healthy")
```

### Logging

All blockchain operations are logged with:
- Transaction hashes
- Operation success/failure
- Performance metrics
- Error details

## Development Setup

### Local Blockchain

1. Start Hardhat network:
```bash
cd blockchain
npx hardhat node --network private
```

2. Deploy contract:
```bash
npx hardhat run scripts/deploy.js --network private
```

3. Update environment variables with deployed contract address

### Testing

Run blockchain integration tests:

```bash
cd backend
pytest tests/test_blockchain_integration.py -v
```

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('web3').setLevel(logging.DEBUG)
logging.getLogger('backend.blockchain_connector').setLevel(logging.DEBUG)
```

## Performance Considerations

### Transaction Costs

- Gas optimization in smart contract calls
- Batch operations where possible
- Efficient data structures in contracts

### Caching

- Network status cached for 30 seconds
- Contract ABI loaded once at startup
- Recent logs cached in memory

### Async Operations

- All blockchain calls are async to prevent blocking
- Connection pooling for RPC calls
- Timeout handling for network operations

## Troubleshooting

### Common Issues

1. **Connection refused**: Check if Hardhat network is running
2. **Contract not found**: Verify CONTRACT_ADDRESS environment variable
3. **Transaction failed**: Check account balance and nonce
4. **ABI not found**: Ensure contract artifacts are built

### Logs Location

- Application logs: `backend/logs/app.log`
- Blockchain logs: `blockchain/logs/`
- Hardhat logs: Console output from `npx hardhat node`

### Recovery Procedures

1. **Restart blockchain network**:
```bash
cd blockchain
npx hardhat node --network private
```

2. **Redeploy contract**:
```bash
npx hardhat run scripts/deploy.js --network private
```

3. **Reset database sync** (if needed):
```bash
# Clear any cached blockchain state
# Restart backend services
```

## Future Enhancements

- **Multi-chain support**: Support for multiple blockchain networks
- **Gas optimization**: Dynamic gas pricing
- **Event streaming**: Real-time event subscriptions
- **Off-chain storage**: IPFS integration for large metadata
- **Cross-chain bridges**: Interoperability with other blockchains