/**
 * Contract Setup Script
 * Initializes deployed contract with authorized loggers and configuration
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("=".repeat(60));
    console.log("AEGIS AUDIT CONTRACT SETUP");
    console.log("=".repeat(60));

    const signers = await hre.ethers.getSigners();
    const deployer = signers[0];
    console.log(`\nSetup account: ${deployer.address}`);

    // Get deployment info
    const deploymentFile = path.join(
        __dirname,
        "../deployments",
        `${hre.network.name}-deployment.json`
    );

    if (!fs.existsSync(deploymentFile)) {
        console.error("❌ Deployment file not found. Run deploy.js first.");
        process.exit(1);
    }

    const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
    const contractAddress = deployment.AegisAudit;

    console.log(`\nConnecting to contract at: ${contractAddress}`);

    // Get contract instance
    const AegisAudit = await hre.ethers.getContractFactory("AegisAudit");
    const contract = AegisAudit.attach(contractAddress);

    // Add sample authorized loggers (backend API addresses)
    const authorizedLoggers = [
        // Note: deployer.address is already authorized by constructor
        // Add additional addresses as needed during actual deployment
    ];

    console.log("\n📝 Authorizing loggers...");
    for (const logger of authorizedLoggers) {
        try {
            // Check if already authorized
            const isAuthorized = await contract.authorizedLoggers(logger);
            if (!isAuthorized && logger !== deployer.address) {
                const tx = await contract.addAuthorizedLogger(logger);
                await tx.wait();
                console.log(`✅ Authorized: ${logger}`);
            } else {
                console.log(`✓ Already authorized: ${logger}`);
            }
        } catch (error) {
            console.error(`❌ Failed to authorize ${logger}: ${error.message}`);
        }
    }

    console.log("\n✨ Setup complete!");
    console.log("Contract is ready to accept log entries from authorized sources.");
    console.log("=".repeat(60));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
