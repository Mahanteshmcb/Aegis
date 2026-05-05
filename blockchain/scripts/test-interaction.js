/**
 * Quick contract interaction test after deployment
 * Usage: npx hardhat run scripts/test-interaction.js --network hardhat
 */

const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("🔍 Testing AEGIS Audit Contract Interactions");
    console.log("=".repeat(50));

    // Get the deployed contract
    const deployment = require("../deployments/hardhat-deployment.json");
    const aegisAudit = await hre.ethers.getContractAt("AegisAudit", deployment.AegisAudit);

    console.log(`📍 Contract Address: ${aegisAudit.address}`);
    console.log(`👤 Owner: ${await aegisAudit.owner()}`);
    console.log(`📊 Initial Log Count: ${await aegisAudit.getLogCount()}`);

    // Test basic logging functionality
    console.log("\n📝 Testing Log Creation...");

    const [signer] = await hre.ethers.getSigners();
    console.log(`🔑 Using account: ${signer.address}`);

    // Create a test log
    const tx = await aegisAudit.createLog(
        signer.address,
        "DEVICE_ACTIVATED",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Test sensor data")),
        "Test device activation",
        1 // tenantId
    );

    await tx.wait();
    console.log("✅ Log created successfully!");

    // Check updated log count
    const newLogCount = await aegisAudit.getLogCount();
    console.log(`📊 New Log Count: ${newLogCount}`);

    // Get the log details
    const logDetails = await aegisAudit.getLog(0);
    console.log("📋 Log Details:");
    console.log(`   ID: ${logDetails.id}`);
    console.log(`   Actor: ${logDetails.actor}`);
    console.log(`   Event Type: ${logDetails.eventType}`);
    console.log(`   Tenant ID: ${logDetails.tenantId}`);
    console.log(`   Severity: ${logDetails.severity}`);
    console.log(`   Verified: ${logDetails.verified}`);

    // Test compliance summary
    const compliance = await aegisAudit.getComplianceSummary(1);
    console.log("\n📊 Compliance Summary for Tenant 1:");
    console.log(`   Total Logs: ${compliance.totalLogs}`);
    console.log(`   Verified Logs: ${compliance.verifiedLogs}`);
    console.log(`   Critical Logs: ${compliance.criticalLogs}`);
    console.log(`   Emergency Logs: ${compliance.emergencyLogs}`);

    // Test audit statistics
    const stats = await aegisAudit.getAuditStatistics();
    console.log("\n📈 Audit Statistics:");
    console.log(`   Total Logs: ${stats.totalLogs}`);
    console.log(`   Total Tenants: ${stats.totalTenants}`);
    console.log(`   Emergency Count: ${stats.emergencyCount}`);
    console.log(`   Average Severity: ${stats.avgSeverity}`);

    console.log("\n" + "=".repeat(50));
    console.log("✅ All contract interactions working correctly!");
    console.log("=".repeat(50));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });