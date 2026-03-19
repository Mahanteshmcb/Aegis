// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract AegisAudit {
    struct AuditLog {
        uint256 timestamp;
        string eventType;
        string dataHash;
        address actor;
    }

    AuditLog[] public logs;

    event LogEntry(uint256 indexed id, uint256 timestamp, string eventType, string dataHash, address actor);

    function addLog(string memory _eventType, string memory _dataHash) public {
        logs.push(AuditLog(block.timestamp, _eventType, _dataHash, msg.sender));
        emit LogEntry(logs.length - 1, block.timestamp, _eventType, _dataHash, msg.sender);
    }

    function getLogCount() public view returns (uint256) {
        return logs.length;
    }
}