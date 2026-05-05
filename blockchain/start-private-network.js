#!/usr/bin/env node

/**
 * AEGIS Private Network Launcher
 * Starts a local private blockchain network for development/testing
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting AEGIS Private Blockchain Network...');
console.log('=' .repeat(50));

// Start Hardhat node
const hardhatProcess = spawn('npx', ['hardhat', 'node'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    shell: true
});

console.log('📡 Private network running on http://127.0.0.1:8545');
console.log('🔑 Chain ID: 31337');
console.log('👥 10 test accounts available');
console.log('');
console.log('📋 Next steps:');
console.log('1. Deploy contract: npm run deploy');
console.log('2. Run demo: npx hardhat run scripts/multi-customer-demo.js --network hardhat');
console.log('3. Test interactions: npx hardhat run scripts/deploy-and-test.js --network hardhat');
console.log('');
console.log('Press Ctrl+C to stop the network');

// Handle process termination
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down private network...');
    hardhatProcess.kill('SIGINT');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down private network...');
    hardhatProcess.kill('SIGTERM');
    process.exit(0);
});