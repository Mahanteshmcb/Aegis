// Test fixtures and helpers for AEGIS Audit contract tests

const { ethers } = require("hardhat");

const TEST_EVENT_TYPES = {
    DEVICE_ACTIVATED: "DEVICE_ACTIVATED",
    DEVICE_DEACTIVATED: "DEVICE_DEACTIVATED",
    DATA_MODIFIED: "DATA_MODIFIED",
    UNAUTHORIZED_ACCESS: "UNAUTHORIZED_ACCESS",
    SENSOR_READING: "SENSOR_READING",
    ZONE_CREATED: "ZONE_CREATED",
    ZONE_UPDATED: "ZONE_UPDATED",
    USER_LOGIN: "USER_LOGIN",
    USER_LOGOUT: "USER_LOGOUT",
    PERMISSION_CHANGED: "PERMISSION_CHANGED",
};

/**
 * Creates a sample data hash
 * @param {string} data - Data to hash
 * @returns {string} Keccak256 hash
 */
function createDataHash(data) {
    return ethers.utils.keccak256(ethers.utils.toUtf8Bytes(data));
}

/**
 * Creates sample metadata
 * @param {object} metadata - Metadata object
 * @returns {string} JSON stringified metadata
 */
function createMetadata(metadata) {
    return JSON.stringify(metadata);
}

/**
 * Sample log creation parameters
 */
const sampleLogs = [
    {
        eventType: TEST_EVENT_TYPES.DEVICE_ACTIVATED,
        dataHash: createDataHash("device-1-activated"),
        metadata: createMetadata({ deviceId: "device-1", status: "online" }),
        tenantId: 1,
    },
    {
        eventType: TEST_EVENT_TYPES.SENSOR_READING,
        dataHash: createDataHash("sensor-reading-1"),
        metadata: createMetadata({ sensorId: "sensor-1", value: 23.5, unit: "C" }),
        tenantId: 1,
    },
    {
        eventType: TEST_EVENT_TYPES.DATA_MODIFIED,
        dataHash: createDataHash("data-modified-1"),
        metadata: createMetadata({ entityId: "entity-1", changes: { status: "active" } }),
        tenantId: 2,
    },
    {
        eventType: TEST_EVENT_TYPES.USER_LOGIN,
        dataHash: createDataHash("user-login-1"),
        metadata: createMetadata({ userId: "user-1", timestamp: Date.now() }),
        tenantId: 1,
    },
];

/**
 * Deploys AegisAudit contract
 * @returns {Promise<Contract>} Deployed contract instance
 */
async function deployContract() {
    const AegisAudit = await ethers.getContractFactory("AegisAudit");
    const contract = await AegisAudit.deploy();
    await contract.deployed();
    return contract;
}

/**
 * Creates multiple log entries
 * @param {Contract} contract - Contract instance
 * @param {object[]} logs - Array of log objects
 * @returns {Promise<string[]>} Array of log IDs
 */
async function createLogs(contract, logs) {
    const logIds = [];
    for (const log of logs) {
        const tx = await contract.createLog(
            log.eventType,
            log.dataHash,
            log.metadata,
            log.tenantId
        );
        logIds.push(tx.hash);
    }
    return logIds;
}

module.exports = {
    TEST_EVENT_TYPES,
    createDataHash,
    createMetadata,
    sampleLogs,
    deployContract,
    createLogs,
};
