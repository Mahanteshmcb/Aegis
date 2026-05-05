const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AegisAudit Enhanced Features", function () {
    let aegisAudit;
    let owner;
    let addr1;
    let addr2;

    beforeEach(async function () {
        [owner, addr1, addr2] = await ethers.getSigners();
        const AegisAudit = await ethers.getContractFactory("AegisAudit");
        aegisAudit = await AegisAudit.deploy();
        await aegisAudit.deployed();
    });

    describe("Severity Levels", function () {
        it("Should create log with INFO severity (default)", async function () {
            const eventType = "INFO_EVENT";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("info"));
            const tenantId = 1;

            const tx = await aegisAudit["createLog(string,bytes32,string,uint256)"](
                eventType,
                dataHash,
                "{}",
                tenantId
            );
            await expect(tx).to.emit(aegisAudit, "LogCreated");

            expect(await aegisAudit.getLogCount()).to.equal(1);
        });

        it("Should create log with custom severity level", async function () {
            const eventType = "ERROR_EVENT";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("error"));
            const tenantId = 1;
            const severity = 2; // ERROR

            const tx = await aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                eventType,
                dataHash,
                "{}",
                tenantId,
                severity
            );
            await expect(tx).to.emit(aegisAudit, "LogCreated");

            expect(await aegisAudit.getLogCount()).to.equal(1);
        });

        it("Should reject invalid severity level", async function () {
            const eventType = "INVALID_SEVERITY";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test"));
            const tenantId = 1;
            const invalidSeverity = 5;

            await expect(
                aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                    eventType,
                    dataHash,
                    "{}",
                    tenantId,
                    invalidSeverity
                )
            ).to.be.revertedWith("Invalid severity level");
        });
    });

    describe("Emergency Logging", function () {
        it("Should create emergency log with CRITICAL severity", async function () {
            const eventType = "EMERGENCY_ALERT";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("emergency"));
            const tenantId = 1;

            const tx = await aegisAudit.emergencyLog(
                eventType,
                dataHash,
                '{"alert": "critical"}',
                tenantId
            );

            await expect(tx).to.emit(aegisAudit, "EmergencyLogCreated");

            expect(await aegisAudit.getEmergencyLogCount()).to.equal(1);
        });

        it("Should toggle emergency mode", async function () {
            await expect(aegisAudit.setEmergencyMode(true))
                .to.emit(aegisAudit, "EmergencyModeChanged")
                .withArgs(true, owner.address);

            expect(await aegisAudit.isEmergencyMode()).to.be.true;

            await expect(aegisAudit.setEmergencyMode(false))
                .to.emit(aegisAudit, "EmergencyModeChanged")
                .withArgs(false, owner.address);

            expect(await aegisAudit.isEmergencyMode()).to.be.false;
        });

        it("Should only allow owner to set emergency mode", async function () {
            await expect(
                aegisAudit.connect(addr1).setEmergencyMode(true)
            ).to.be.revertedWith("Only owner can call this function");
        });
    });

    describe("Batch Log Creation", function () {
        it("Should create multiple logs in batch", async function () {
            const entries = [
                {
                    eventType: "BATCH_EVENT_1",
                    dataHash: ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data1")),
                    metadata: '{"id": 1}',
                    severity: 0
                },
                {
                    eventType: "BATCH_EVENT_2",
                    dataHash: ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data2")),
                    metadata: '{"id": 2}',
                    severity: 1
                }
            ];
            const tenantId = 1;

            const tx = await aegisAudit.batchCreateLogs(entries, tenantId);

            await expect(tx).to.emit(aegisAudit, "BatchLogsCreated");

            expect(await aegisAudit.getLogCount()).to.equal(2);
        });

        it("Should reject batch with more than 50 entries", async function () {
            const entries = Array(51).fill({
                eventType: "EVENT",
                dataHash: ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data")),
                metadata: "{}",
                severity: 0
            });

            await expect(
                aegisAudit.batchCreateLogs(entries, 1)
            ).to.be.revertedWith("Maximum 50 entries per batch");
        });
    });

    describe("Enhanced Query Functions", function () {
        beforeEach(async function () {
            // Create logs with different event types and actors
            const dataHash1 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data1"));
            const dataHash2 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data2"));
            const dataHash3 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data3"));

            // Create with different severity levels
            await aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                "DEVICE_ACTIVATED",
                dataHash1,
                "{}",
                1,
                0
            );
            await aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                "DEVICE_ACTIVATED",
                dataHash2,
                "{}",
                1,
                2
            );
            await aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                "DEVICE_DEACTIVATED",
                dataHash3,
                "{}",
                1,
                1
            );

            // Create with addr1
            await aegisAudit.addAuthorizedLogger(addr1.address);
            const dataHash4 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data4"));
            await aegisAudit.connect(addr1)["createLog(string,bytes32,string,uint256,uint8)"](
                "SENSOR_DATA",
                dataHash4,
                "{}",
                2,
                0
            );
        });

        it("Should get logs by event type", async function () {
            const activatedLogs = await aegisAudit.getLogsByEventType("DEVICE_ACTIVATED");
            expect(activatedLogs.length).to.equal(2);

            const deactivatedLogs = await aegisAudit.getLogsByEventType("DEVICE_DEACTIVATED");
            expect(deactivatedLogs.length).to.equal(1);
        });

        it("Should get logs by actor address", async function () {
            const ownerLogs = await aegisAudit.getLogsByActor(owner.address);
            expect(ownerLogs.length).to.equal(3);

            const addr1Logs = await aegisAudit.getLogsByActor(addr1.address);
            expect(addr1Logs.length).to.equal(1);
        });

        it("Should get logs by severity level", async function () {
            const infoLogs = await aegisAudit.getLogsBySeverity(0); // INFO
            expect(infoLogs.length).to.equal(2);

            const errorLogs = await aegisAudit.getLogsBySeverity(2); // ERROR
            expect(errorLogs.length).to.equal(1);

            const warningLogs = await aegisAudit.getLogsBySeverity(1); // WARNING
            expect(warningLogs.length).to.equal(1);
        });

        it("Should get recent logs", async function () {
            const recent2 = await aegisAudit.getRecentLogs(2);
            expect(recent2.length).to.equal(2);

            const recent10 = await aegisAudit.getRecentLogs(10);
            expect(recent10.length).to.equal(4); // Only 4 total logs exist
        });

        it("Should get logs by time range", async function () {
            const now = Math.floor(Date.now() / 1000);
            const logsInRange = await aegisAudit.getLogsByTimeRange(
                now - 3600, // 1 hour ago
                now + 3600  // 1 hour from now
            );
            expect(logsInRange.length).to.be.greaterThan(0);
        });
    });

    describe("Compliance Reporting", function () {
        beforeEach(async function () {
            const dataHash1 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data1"));
            const dataHash2 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data2"));

            // Create logs with different severity levels
            await aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                "EVENT_1",
                dataHash1,
                "{}",
                1,
                0
            );
            await aegisAudit["createLog(string,bytes32,string,uint256,uint8)"](
                "EVENT_2",
                dataHash2,
                "{}",
                1,
                3
            );
        });

        it("Should generate compliance summary for tenant", async function () {
            const summary = await aegisAudit.getComplianceSummary(1);
            expect(summary.totalLogs).to.equal(2);
            expect(summary.verifiedLogs).to.equal(2);
            expect(summary.criticalLogs).to.equal(1);
        });

        it("Should get audit statistics", async function () {
            const stats = await aegisAudit.getAuditStatistics();
            expect(stats.totalLogs.toString()).to.equal("2");
            expect(stats.totalTenants.toNumber()).to.be.greaterThan(0);
            expect(stats.avgSeverity.toNumber()).to.equal(1); // (0 + 3) / 2 = 1
        });
    });

    describe("Archive and Utility Functions", function () {
        it("Should archive log entry", async function () {
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data"));
            const tx = await aegisAudit["createLog(string,bytes32,string,uint256)"](
                "EVENT",
                dataHash,
                "{}",
                1
            );
            const receipt = await tx.wait();
            const logId = receipt.events[0].args[0];

            const logBefore = await aegisAudit.getLog(logId);
            expect(logBefore.archived).to.be.false;

            await aegisAudit.archiveLog(logId);

            const logAfter = await aegisAudit.getLog(logId);
            expect(logAfter.archived).to.be.true;
        });

        it("Should only allow owner to archive logs", async function () {
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data"));
            const tx = await aegisAudit["createLog(string,bytes32,string,uint256)"](
                "EVENT",
                dataHash,
                "{}",
                1
            );
            const receipt = await tx.wait();
            const logId = receipt.events[0].args[0];

            await expect(
                aegisAudit.connect(addr1).archiveLog(logId)
            ).to.be.revertedWith("Only owner can call this function");
        });

        it("Should get emergency log count", async function () {
            const countBefore = await aegisAudit.getEmergencyLogCount();

            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("emergency"));
            await aegisAudit.emergencyLog("EMERGENCY", dataHash, "{}", 1);

            const countAfter = await aegisAudit.getEmergencyLogCount();
            expect(countAfter).to.equal(countBefore.add(1));
        });
    });
});
