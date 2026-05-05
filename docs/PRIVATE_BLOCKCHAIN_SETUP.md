# AEGIS Private Blockchain Network Setup

## Overview
AEGIS implements a **fully offline private blockchain network** where multiple customers can connect, request requirements, and other network participants can manually accept or reject those requests. All interactions are recorded immutably on the blockchain for audit trails.

## Architecture

### Network Configuration
- **Chain ID**: 12345 (custom private network)
- **Consensus**: Proof of Authority (private network)
- **Nodes**: Multiple customer-operated nodes
- **Access**: Permissioned network (authorized participants only)

### Smart Contract Features
- **Multi-tenant isolation**: Each customer has their own tenant space
- **Requirement lifecycle**: REQUEST → APPROVE/REJECT → IMPLEMENT
- **Emergency handling**: Critical requests with priority processing
- **Audit trails**: Immutable logs of all interactions
- **Event subscriptions**: Real-time notifications for requirement updates

## Requirement Workflow

### 1. Request Submission
```
Customer A → Blockchain: "REQUIREMENT_REQUEST"
- Event Type: REQUIREMENT_REQUEST
- Details: Sensor installation needed
- Tenant: Customer A's tenant ID
- Severity: INFO (normal request)
```

### 2. Manual Review & Decision
```
Customer B → Blockchain: "REQUIREMENT_APPROVAL" or "REQUIREMENT_REJECTION"
- Event Type: REQUIREMENT_APPROVAL/REJECTION
- References: Original request details
- Decision: Accept or reject with reasoning
- Tenant: Same as request
```

### 3. Emergency Requests
```
Any Customer → Blockchain: "EMERGENCY_REQUEST"
- Event Type: EMERGENCY_REQUEST
- Severity: CRITICAL (highest priority)
- Requires immediate attention
- Emergency counter incremented
```

## Network Setup Instructions

### 1. Local Development Network
```bash
# Start local Hardhat network (simulates private network)
npx hardhat node

# Deploy contract to local network
npm run deploy
```

### 2. Multi-Node Private Network Setup
```bash
# Each customer runs their own node
npx hardhat node --port 8545  # Customer 1
npx hardhat node --port 8546  # Customer 2
# ... etc
```

### 3. Contract Deployment
```javascript
// Deploy to private network
npx hardhat run scripts/deploy.js --network private
```

## Customer Interaction Examples

### Requesting Requirements
```javascript
// Customer submits requirement
await contract.createLog(
    "REQUIREMENT_REQUEST",
    hashOfDetails,
    "Need temperature sensor in Zone A",
    customerTenantId
);
```

### Approving/Rejecting Requests
```javascript
// Network participant approves
await contract.createLog(
    "REQUIREMENT_APPROVAL",
    hashOfDecision,
    "Approved - will install next week",
    requestTenantId
);

// Or rejects
await contract.createLog(
    "REQUIREMENT_REJECTION",
    hashOfDecision,
    "Rejected - maintenance scheduled",
    requestTenantId
);
```

## Monitoring & Analytics

### Real-time Tracking
- **Event Subscriptions**: Subscribe to requirement events
- **Live Updates**: Get notified of new requests/decisions
- **Dashboard**: View all requirements by status

### Analytics Queries
```javascript
// Get all pending requests
const requests = await contract.getLogsByEventType("REQUIREMENT_REQUEST");

// Get approval rate for tenant
const compliance = await contract.getComplianceSummary(tenantId);

// Get emergency statistics
const stats = await contract.getAuditStatistics();
```

## Security & Privacy

### Private Network Benefits
- **No public exposure**: Completely offline operation
- **Controlled access**: Only authorized customers participate
- **Data privacy**: Requirements stay within private network
- **Audit compliance**: Immutable logs for regulatory requirements

### Access Control
- **Authorized loggers**: Only verified customers can submit logs
- **Owner controls**: Network administrator manages authorizations
- **Tenant isolation**: Customers only see their relevant data

## Deployment Scenarios

### Development
```bash
npm run deploy  # Deploys to hardhat network
```

### Private Network
```bash
# Update hardhat.config.js with private network URL
npm run deploy:private  # Custom script for private deployment
```

### Production Private Network
- Multiple physical nodes across customer locations
- VPN or private network connectivity
- Automated deployment scripts
- Backup and recovery procedures

## Integration with AEGIS Platform

### Backend Integration
- REST API endpoints for requirement submission
- WebSocket connections for real-time updates
- Database synchronization with blockchain state

### Frontend Features
- Requirement submission forms
- Approval/rejection interfaces
- Real-time notification system
- Analytics dashboard

### IoT Integration
- Sensor data validation through blockchain
- Automated requirement generation
- Maintenance scheduling based on approvals

## Future Enhancements

### Advanced Features
- **Smart contract upgrades**: Proxy patterns for contract updates
- **Multi-signature approvals**: Require multiple approvals for critical requests
- **Automated workflows**: Smart contract logic for routine approvals
- **Token incentives**: Reward system for active network participation

### Scaling Considerations
- **Layer 2 solutions**: For high-volume requirement networks
- **Sharding**: Distribute load across multiple chains
- **Cross-chain**: Connect multiple private networks

This private blockchain setup provides a secure, transparent, and efficient way for multiple customers to collaborate on requirements while maintaining complete control over their data and operations.