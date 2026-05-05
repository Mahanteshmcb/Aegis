/**
 * Multi-Customer Requirement Request System Demo
 * Shows how multiple customers can request requirements and others can accept/reject
 * Usage: npx hardhat run scripts/multi-customer-demo.js --network hardhat
 */

const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("🏢 AEGIS Multi-Customer Requirement System Demo");
    console.log("=".repeat(60));

    // Get multiple customer accounts (simulating different customers in private network)
    const customers = await hre.ethers.getSigners();
    console.log(`👥 ${customers.length} customers available in private network`);

    // Deploy AegisAudit contract
    console.log("\n📦 Deploying AegisAudit contract...");
    const AegisAudit = await hre.ethers.getContractFactory("AegisAudit");
    const aegisAudit = await AegisAudit.deploy();
    await aegisAudit.deployed();

    console.log(`✅ Contract deployed to: ${aegisAudit.address}`);

    // Authorize all customers as loggers (in private network, all participants are trusted)
    console.log("\n🔐 Authorizing all customers...");
    for (let i = 1; i < customers.length; i++) {
        await aegisAudit.addAuthorizedLogger(customers[i].address);
        console.log(`✅ Customer ${i} authorized: ${customers[i].address.substring(0, 10)}...`);
    }

    // Simulate requirement requests and responses
    console.log("\n📋 SIMULATING REQUIREMENT REQUESTS & RESPONSES");
    console.log("-".repeat(50));

    // Customer 1 requests a sensor installation
    console.log("\n1️⃣ Customer 1 requests: SENSOR_INSTALLATION");
    const request1 = await aegisAudit.connect(customers[1])['createLog(string,bytes32,string,uint256)'](
        "REQUIREMENT_REQUEST",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Sensor installation needed")),
        "Customer 1 needs temperature sensor installed in Zone A",
        1 // tenantId
    );
    await request1.wait();
    console.log("✅ Request logged by Customer 1");

    // Customer 2 accepts the request
    console.log("\n2️⃣ Customer 2 accepts: APPROVAL_GRANTED");
    const approval1 = await aegisAudit.connect(customers[2])['createLog(string,bytes32,string,uint256)'](
        "REQUIREMENT_APPROVAL",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Approved sensor installation")),
        "Customer 2 approves sensor installation for Customer 1",
        1
    );
    await approval1.wait();
    console.log("✅ Approval logged by Customer 2");

    // Customer 3 requests maintenance
    console.log("\n3️⃣ Customer 3 requests: MAINTENANCE_REQUIRED");
    const request2 = await aegisAudit.connect(customers[3])['createLog(string,bytes32,string,uint256)'](
        "REQUIREMENT_REQUEST",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Maintenance required")),
        "Customer 3 needs urgent maintenance on IoT gateway",
        2 // different tenant
    );
    await request2.wait();
    console.log("✅ Request logged by Customer 3");

    // Customer 4 rejects the maintenance request
    console.log("\n4️⃣ Customer 4 rejects: APPROVAL_DENIED");
    const rejection1 = await aegisAudit.connect(customers[4])['createLog(string,bytes32,string,uint256)'](
        "REQUIREMENT_REJECTION",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Maintenance rejected")),
        "Customer 4 rejects maintenance request - scheduled for next week",
        2
    );
    await rejection1.wait();
    console.log("✅ Rejection logged by Customer 4");

    // Customer 5 requests emergency access
    console.log("\n5️⃣ Customer 5 requests: EMERGENCY_ACCESS");
    const emergencyRequest = await aegisAudit.connect(customers[5])['emergencyLog(string,bytes32,string,uint256)'](
        "EMERGENCY_REQUEST",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Emergency system access")),
        "Customer 5 needs immediate emergency access to control systems",
        3
    );
    await emergencyRequest.wait();
    console.log("🚨 Emergency request logged by Customer 5");

    // Customer 1 approves emergency access
    console.log("\n6️⃣ Customer 1 approves: EMERGENCY_APPROVED");
    const emergencyApproval = await aegisAudit.connect(customers[1])['createLog(string,bytes32,string,uint256,uint8)'](
        "EMERGENCY_APPROVAL",
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Emergency access granted")),
        "Customer 1 approves emergency access for Customer 5",
        3,
        3 // CRITICAL severity
    );
    await emergencyApproval.wait();
    console.log("✅ Emergency approval logged by Customer 1");

    // Get system statistics
    console.log("\n📊 SYSTEM STATISTICS");
    console.log("-".repeat(30));

    const totalLogs = await aegisAudit.getLogCount();
    console.log(`📈 Total Requirements Logged: ${totalLogs}`);

    const stats = await aegisAudit.getAuditStatistics();
    console.log(`🏢 Total Tenants: ${stats.totalTenants}`);
    console.log(`🚨 Emergency Events: ${stats.emergencyCount}`);
    console.log(`📊 Average Severity: ${stats.avgSeverity}`);

    // Get compliance summary for each tenant
    for (let tenantId = 1; tenantId <= 3; tenantId++) {
        const compliance = await aegisAudit.getComplianceSummary(tenantId);
        console.log(`\n🏢 Tenant ${tenantId} Compliance:`);
        console.log(`   Total Logs: ${compliance.totalLogs}`);
        console.log(`   Verified: ${compliance.verifiedLogs}`);
        console.log(`   Critical: ${compliance.criticalLogs}`);
        console.log(`   Emergency: ${compliance.emergencyLogs}`);
    }

    // Demonstrate requirement tracking
    console.log("\n🔍 REQUIREMENT TRACKING EXAMPLES");
    console.log("-".repeat(35));

    // Get all requirement requests
    const requestLogs = await aegisAudit.getLogsByEventType("REQUIREMENT_REQUEST");
    console.log(`📋 Total Requirement Requests: ${requestLogs.length}`);

    // Get all approvals
    const approvalLogs = await aegisAudit.getLogsByEventType("REQUIREMENT_APPROVAL");
    console.log(`✅ Total Approvals: ${approvalLogs.length}`);

    // Get all rejections
    const rejectionLogs = await aegisAudit.getLogsByEventType("REQUIREMENT_REJECTION");
    console.log(`❌ Total Rejections: ${rejectionLogs.length}`);

    // Get recent logs (last 10)
    const recentLogs = await aegisAudit.getRecentLogs(10);
    console.log(`\n🕐 Recent Activity (last ${recentLogs.length} logs):`);
    for (let i = 0; i < Math.min(recentLogs.length, 5); i++) {
        const logId = recentLogs[i];
        const logDetails = await aegisAudit.getLog(logId);
        console.log(`   ${i + 1}. ${logDetails.eventType} by ${logDetails.actor.substring(0, 10)}...`);
    }

    console.log("\n" + "=".repeat(60));
    console.log("🎉 PRIVATE NETWORK DEMO COMPLETE!");
    console.log("=".repeat(60));
    console.log("✅ Multi-customer requirement system working");
    console.log("✅ Request/Approve/Reject workflow functional");
    console.log("✅ Emergency handling operational");
    console.log("✅ Audit trail immutable and traceable");
    console.log("✅ All customers can participate equally");
    console.log("\n🚀 Ready for your offline private blockchain network!");
    console.log("=".repeat(60));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Error:", error);
        process.exit(1);
    });