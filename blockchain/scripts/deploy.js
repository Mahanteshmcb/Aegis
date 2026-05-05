/**
 * Deployment script for AEGIS Audit Contract
 * Usage: npx hardhat run scripts/deploy.js --network localhost
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("=".repeat(60));
    console.log("AEGIS AUDIT CONTRACT DEPLOYMENT");
    console.log("=".repeat(60));

    // Get deployer account
    const signers = await hre.ethers.getSigners();
    const deployer = signers[0];
    console.log(`\nDeploying contracts with account: ${deployer.address}`);
    console.log(`Account balance: ${(await deployer.getBalance()).toString()}`);

    // Deploy AegisAudit contract
    console.log("\n📦 Deploying AegisAudit contract...");
    const AegisAudit = await hre.ethers.getContractFactory("AegisAudit");
    const aegisAudit = await AegisAudit.deploy();
    await aegisAudit.deployed();

    console.log(`✅ AegisAudit deployed to: ${aegisAudit.address}`);

    // Get deployment details
    const deploymentInfo = {
        network: hre.network.name,
        deployer: deployer.address,
        AegisAudit: aegisAudit.address,
        deploymentTime: new Date().toISOString(),
        blockNumber: await hre.ethers.provider.getBlockNumber(),
    };

    console.log("\n📋 Deployment Summary:");
    console.log(JSON.stringify(deploymentInfo, null, 2));

    // Save deployment info
    const deploymentsDir = path.join(__dirname, "../deployments");
    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
    }

    const deploymentFile = path.join(
        deploymentsDir,
        `${hre.network.name}-deployment.json`
    );
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    console.log(`\n💾 Deployment info saved to: ${deploymentFile}`);

    // Get contract info
    console.log("\n📖 Contract Information:");
    console.log(`Address: ${aegisAudit.address}`);
    console.log(`Owner: ${await aegisAudit.owner()}`);
    console.log(`Initial log count: ${await aegisAudit.getLogCount()}`);

    console.log("\n" + "=".repeat(60));
    console.log("Deployment complete! ✨");
    console.log("=".repeat(60));

    // Return contract address for testing
    return aegisAudit.address;
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
