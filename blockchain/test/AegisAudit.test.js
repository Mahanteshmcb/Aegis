const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AegisAudit Contract", function () {
    let aegisAudit;
    let owner;
    let addr1;
    let addr2;
    let addrs;

    beforeEach(async function () {
        // Get signers
        [owner, addr1, addr2, ...addrs] = await ethers.getSigners();

        // Deploy contract
        const AegisAudit = await ethers.getContractFactory("AegisAudit");
        aegisAudit = await AegisAudit.deploy();
        await aegisAudit.deployed();
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await aegisAudit.owner()).to.equal(owner.address);
        });

        it("Should initialize with zero logs", async function () {
            expect(await aegisAudit.getLogCount()).to.equal(0);
        });

        it("Should authorize owner as logger", async function () {
            expect(await aegisAudit.authorizedLoggers(owner.address)).to.be.true;
        });
    });

    describe("Authorized Logger Management", function () {
        it("Should allow owner to add authorized logger", async function () {
            await expect(aegisAudit.addAuthorizedLogger(addr1.address))
                .to.emit(aegisAudit, "AuthorizerAdded")
                .withArgs(addr1.address);

            expect(await aegisAudit.authorizedLoggers(addr1.address)).to.be.true;
        });

        it("Should not allow non-owner to add logger", async function () {
            await expect(
                aegisAudit.connect(addr1).addAuthorizedLogger(addr2.address)
            ).to.be.revertedWith("Only owner can call this function");
        });

        it("Should not allow adding zero address", async function () {
            await expect(
                aegisAudit.addAuthorizedLogger(ethers.constants.AddressZero)
            ).to.be.revertedWith("Invalid address");
        });

        it("Should not allow adding already authorized logger", async function () {
            await aegisAudit.addAuthorizedLogger(addr1.address);
            await expect(
                aegisAudit.addAuthorizedLogger(addr1.address)
            ).to.be.revertedWith("Already authorized");
        });

        it("Should allow owner to remove authorized logger", async function () {
            await aegisAudit.addAuthorizedLogger(addr1.address);
            await expect(aegisAudit.removeAuthorizedLogger(addr1.address))
                .to.emit(aegisAudit, "AuthorizerRemoved")
                .withArgs(addr1.address);

            expect(await aegisAudit.authorizedLoggers(addr1.address)).to.be.false;
        });

        it("Should not allow removing owner", async function () {
            await expect(
                aegisAudit.removeAuthorizedLogger(owner.address)
            ).to.be.revertedWith("Cannot remove owner");
        });
    });

    describe("Log Creation", function () {
        it("Should create log entry from authorized logger", async function () {
            const eventType = "DEVICE_ACTIVATED";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test-data"));
            const metadata = '{"deviceId": "device-1"}';
            const tenantId = 1;

            const tx = await aegisAudit.createLog(
                eventType,
                dataHash,
                metadata,
                tenantId
            );

            await expect(tx)
                .to.emit(aegisAudit, "LogCreated")
                .withArgs(
                    await tx.then(t => t.wait().then(r => r.transactionHash)),
                    tenantId,
                    owner.address,
                    eventType
                );

            expect(await aegisAudit.getLogCount()).to.equal(1);
        });

        it("Should create log with correct data", async function () {
            const eventType = "DATA_MODIFIED";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data-hash"));
            const metadata = '{"changes": "value"}';
            const tenantId = 1;

            const tx = await aegisAudit.createLog(
                eventType,
                dataHash,
                metadata,
                tenantId
            );

            const receipt = await tx.wait();
            const logId = ethers.utils.keccak256(
                ethers.utils.solidityPack(
                    ["address", "uint256", "uint256", "uint256"],
                    [owner.address, receipt.blockNumber, receipt.blockNumber, 0]
                )
            );

            // Log created successfully
            expect(await aegisAudit.getLogCount()).to.equal(1);
        });

        it("Should not allow unauthorized address to create log", async function () {
            const eventType = "UNAUTHORIZED_ACCESS";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test"));
            const metadata = "{}";
            const tenantId = 1;

            await expect(
                aegisAudit
                    .connect(addr1)
                    .createLog(eventType, dataHash, metadata, tenantId)
            ).to.be.revertedWith("Not authorized to log");
        });

        it("Should not allow empty event type", async function () {
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test"));
            const metadata = "{}";
            const tenantId = 1;

            await expect(
                aegisAudit.createLog("", dataHash, metadata, tenantId)
            ).to.be.revertedWith("Event type required");
        });

        it("Should not allow invalid tenant ID", async function () {
            const eventType = "TEST_EVENT";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test"));
            const metadata = "{}";

            await expect(
                aegisAudit.createLog(eventType, dataHash, metadata, 0)
            ).to.be.revertedWith("Valid tenant ID required");
        });

        it("Should authorize logger and allow logging", async function () {
            await aegisAudit.addAuthorizedLogger(addr1.address);

            const eventType = "DEVICE_ONLINE";
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("online"));
            const metadata = '{"status": "online"}';
            const tenantId = 1;

            const tx = await aegisAudit
                .connect(addr1)
                .createLog(eventType, dataHash, metadata, tenantId);

            expect(tx).to.emit(aegisAudit, "LogCreated");
            expect(await aegisAudit.getLogCount()).to.equal(1);
        });
    });

    describe("Log Querying", function () {
        beforeEach(async function () {
            // Create a few log entries
            const dataHash1 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data1"));
            const dataHash2 = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("data2"));

            await aegisAudit.createLog(
                "EVENT_1",
                dataHash1,
                '{"id": 1}',
                1
            );

            await aegisAudit.createLog(
                "EVENT_2",
                dataHash2,
                '{"id": 2}',
                1
            );

            await aegisAudit.createLog(
                "EVENT_3",
                dataHash1,
                '{"id": 3}',
                2
            );
        });

        it("Should get tenant logs", async function () {
            const tenantLogs = await aegisAudit.getTenantLogs(1);
            expect(tenantLogs.length).to.equal(2);
        });

        it("Should get tenant log count", async function () {
            expect(await aegisAudit.getTenantLogCount(1)).to.equal(2);
            expect(await aegisAudit.getTenantLogCount(2)).to.equal(1);
        });

        it("Should get all logs", async function () {
            const allLogs = await aegisAudit.getAllLogs();
            expect(allLogs.length).to.equal(3);
        });

        it("Should get log count", async function () {
            expect(await aegisAudit.getLogCount()).to.equal(3);
        });
    });

    describe("Log Verification", function () {
        it("Should verify log with correct hash", async function () {
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("verify-test"));
            const tx = await aegisAudit.createLog(
                "TEST_EVENT",
                dataHash,
                "{}",
                1
            );

            const receipt = await tx.wait();
            const logs = await aegisAudit.getAllLogs();
            const logId = logs[0];

            const isValid = await aegisAudit.verifyLog(logId, dataHash);
            expect(isValid).to.be.true;
        });

        it("Should fail verification with incorrect hash", async function () {
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("original"));
            const wrongHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("wrong"));

            const tx = await aegisAudit.createLog(
                "TEST_EVENT",
                dataHash,
                "{}",
                1
            );

            const receipt = await tx.wait();
            const logs = await aegisAudit.getAllLogs();
            const logId = logs[0];

            const isValid = await aegisAudit.verifyLog(logId, wrongHash);
            expect(isValid).to.be.false;
        });
    });

    describe("Ownership Transfer", function () {
        it("Should transfer ownership to new owner", async function () {
            await aegisAudit.transferOwnership(addr1.address);
            expect(await aegisAudit.owner()).to.equal(addr1.address);
        });

        it("Should authorize new owner as logger", async function () {
            await aegisAudit.transferOwnership(addr1.address);
            expect(await aegisAudit.authorizedLoggers(addr1.address)).to.be.true;
        });

        it("Should not allow non-owner to transfer", async function () {
            await expect(
                aegisAudit.connect(addr1).transferOwnership(addr2.address)
            ).to.be.revertedWith("Only owner can call this function");
        });

        it("Should not allow transfer to zero address", async function () {
            await expect(
                aegisAudit.transferOwnership(ethers.constants.AddressZero)
            ).to.be.revertedWith("Invalid address");
        });
    });

    describe("Gas Optimization", function () {
        it("Should create log with reasonable gas", async function () {
            const dataHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("gas-test"));
            const tx = await aegisAudit.createLog(
                "TEST_EVENT",
                dataHash,
                '{"test": true}',
                1
            );

            const receipt = await tx.wait();
            console.log(`Gas used for log creation: ${receipt.gasUsed.toString()}`);
            expect(receipt.gasUsed).to.be.below(200000);
        });
    });
});
