/**
 * Combined deployment and interaction test
 * Usage: npx hardhat run scripts/deploy-and-test.js --network hardhat
 */

const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 AEGIS Audit Contract - Deploy & Test");
    console.log("=".repeat(60));

    // Get deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log(`Deploying with account: ${deployer.address}`);
    console.log(`Account balance: ${(await deployer.getBalance()).toString()}`);

    // Deploy AegisAudit contract
    console.log("\n📦 Deploying AegisAudit contract...");
    const AegisAudit = await hre.ethers.getContractFactory("AegisAudit");
    const aegisAudit = await AegisAudit.deploy();
    await aegisAudit.deployed();

    console.log(`✅ Contract deployed to: ${aegisAudit.address}`);

    // Basic contract info
    console.log(`👤 Owner: ${await aegisAudit.owner()}`);
    console.log(`📊 Initial Log Count: ${await aegisAudit.getLogCount()}`);

    // Check if deployer is already authorized
    const isAuthorized = await aegisAudit.authorizedLoggers(deployer.address);
    console.log(`🔐 Deployer authorized: ${isAuthorized}`);

    if (!isAuthorized) {
        console.log("\n🔐 Adding deployer as authorized logger...");
        await aegisAudit.addAuthorizedLogger(deployer.address);
        console.log("✅ Deployer authorized for logging");
    } else {
        console.log("ℹ️  Deployer already authorized");
    }

    // Test log creation
    console.log("\n📝 Testing Log Creation...");

    // Use the specific overloaded function signature
    const tx = await aegisAudit['createLog(string,bytes32,string,uint256)'](
        "DEVICE_ACTIVATED",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Test sensor data")),
        "Test device activation",
        1 // tenantId
    );

    const receipt = await tx.wait();
    console.log(`✅ Log created! Gas used: ${receipt.gasUsed}`);

    // Verify log was created
    const logCount = await aegisAudit.getLogCount();
    console.log(`📊 Total Logs: ${logCount}`);

    // Get log details - need to get the logId from the event
    const logCreatedEvent = receipt.events?.find(e => e.event === 'LogCreated');
    const logId = logCreatedEvent?.args?.logId;

    if (logId) {
        const logDetails = await aegisAudit.getLog(logId);
        console.log("\n📋 Log Details:");
        console.log(`   ID: ${logDetails.id}`);
        console.log(`   Actor: ${logDetails.actor}`);
        console.log(`   Event Type: ${logDetails.eventType}`);
        console.log(`   Tenant ID: ${logDetails.tenantId}`);
        console.log(`   Severity: ${logDetails.severity}`);
        console.log(`   Verified: ${logDetails.verified}`);
    } else {
        console.log("⚠️  Could not find LogCreated event");
    }

    // Test emergency log
    console.log("\n🚨 Testing Emergency Log...");
    const emergencyTx = await aegisAudit['emergencyLog(string,bytes32,string,uint256)'](
        "SECURITY_ALERT",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Emergency security breach")),
        "Critical security alert detected",
        1
    );
    await emergencyTx.wait();
    console.log("✅ Emergency log created!");

    // Check emergency count
    const emergencyCount = await aegisAudit.getEmergencyLogCount();
    console.log(`🚨 Emergency Log Count: ${emergencyCount}`);

    // Test compliance summary
    const compliance = await aegisAudit.getComplianceSummary(1);
    console.log("\n📊 Compliance Summary for Tenant 1:");
    console.log(`   Total Logs: ${compliance.totalLogs}`);
    console.log(`   Verified Logs: ${compliance.verifiedLogs}`);
    console.log(`   Critical Logs: ${compliance.criticalLogs}`);
    console.log(`   Emergency Logs: ${compliance.emergencyLogs}`);

    // Test audit statistics
    const stats = await aegisAudit.getAuditStatistics();
    console.log("\n📈 System Audit Statistics:");
    console.log(`   Total Logs: ${stats.totalLogs}`);
    console.log(`   Total Tenants: ${stats.totalTenants}`);
    console.log(`   Emergency Count: ${stats.emergencyCount}`);
    console.log(`   Average Severity: ${stats.avgSeverity}`);

    // Test event subscription
    console.log("\n📡 Testing Event Subscription...");
    await aegisAudit.subscribeToEvent("DEVICE_ACTIVATED");
    console.log("✅ Subscribed to DEVICE_ACTIVATED events");

    // Create another log to test subscription
    const subTx = await aegisAudit['createLog(string,bytes32,string,uint256)'](
        "DEVICE_ACTIVATED",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Another test")),
        "Another device activation",
        1
    );
    await subTx.wait();
    console.log("✅ Log created for subscribed event");

    console.log("\n" + "=".repeat(60));
    console.log("🎉 DEPLOYMENT & TESTING COMPLETE!");
    console.log(`📍 Contract Address: ${aegisAudit.address}`);
    console.log(`🔗 Network: ${hre.network.name}`);
    console.log("=".repeat(60));

    // Return contract info for potential use
    return {
        address: aegisAudit.address,
        network: hre.network.name,
        owner: await aegisAudit.owner(),
        logCount: await aegisAudit.getLogCount()
    };
}

main()
    .then((result) => {
        console.log("\n📋 Final Summary:");
        console.log(JSON.stringify(result, null, 2));
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Error:", error);
        process.exit(1);
    });