// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IAegisAudit
 * @dev Enhanced interface for the AEGIS Audit contract
 */
interface IAegisAudit {
    // ==================== STRUCTS ====================
    struct LogEntry {
        uint256 id;
        uint256 timestamp;
        address actor;
        string eventType;
        bytes32 dataHash;
        string metadata;
        uint256 tenantId;
        uint8 severity;
        bool verified;
        bool archived;
    }

    struct BatchLogEntry {
        string eventType;
        bytes32 dataHash;
        string metadata;
        uint8 severity;
    }

    // ==================== EVENTS ====================
    event LogCreated(
        bytes32 indexed logId,
        uint256 indexed tenantId,
        address indexed actor,
        string eventType,
        uint8 severity,
        uint256 timestamp
    );

    event BatchLogsCreated(
        bytes32[] logIds,
        uint256 indexed tenantId,
        address indexed actor,
        uint256 count,
        uint256 timestamp
    );

    event LogVerified(bytes32 indexed logId, bool isValid);
    event EmergencyLogCreated(
        bytes32 indexed logId,
        uint256 indexed tenantId,
        string eventType,
        uint256 timestamp
    );
    event EmergencyModeChanged(bool activated, address indexed actor);
    event AuthorizerAdded(address indexed account);
    event AuthorizerRemoved(address indexed account);
    event EventSubscribed(address indexed subscriber, string eventType);
    event EventUnsubscribed(address indexed subscriber, string eventType);

    // ==================== FUNCTIONS ====================
    // Owner functions
    function addAuthorizedLogger(address _account) external;
    function removeAuthorizedLogger(address _account) external;
    function transferOwnership(address _newOwner) external;
    function setEmergencyMode(bool _activate) external;
    function archiveLog(bytes32 _logId) external;

    // Logging functions
    function createLog(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId
    ) external returns (bytes32);

    function createLog(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId,
        uint8 _severity
    ) external returns (bytes32);

    function batchCreateLogs(
        BatchLogEntry[] memory _entries,
        uint256 _tenantId
    ) external returns (bytes32[] memory);

    function emergencyLog(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId
    ) external returns (bytes32);

    // Query functions
    function getLog(bytes32 _logId) external view returns (LogEntry memory);
    function getTenantLogs(uint256 _tenantId) external view returns (bytes32[] memory);
    function getTenantLogCount(uint256 _tenantId) external view returns (uint256);
    function getAllLogs() external view returns (bytes32[] memory);
    function getLogsByEventType(string memory _eventType) external view returns (bytes32[] memory);
    function getLogsByActor(address _actor) external view returns (bytes32[] memory);
    function getLogsBySeverity(uint8 _severity) external view returns (bytes32[] memory);
    function getRecentLogs(uint256 _count) external view returns (bytes32[] memory);
    function getLogsByTimeRange(uint256 _startTime, uint256 _endTime) external view returns (bytes32[] memory);

    // Verification and compliance
    function verifyLog(bytes32 _logId, bytes32 _expectedHash) external returns (bool);
    function getComplianceSummary(uint256 _tenantId) external view returns (
        uint256 totalLogs,
        uint256 verifiedLogs,
        uint256 criticalLogs,
        uint256 emergencyLogs
    );
    function getAuditStatistics() external view returns (
        uint256 totalLogs,
        uint256 totalTenants,
        uint256 emergencyCount,
        uint256 avgSeverity
    );

    // Event subscription
    function subscribeToEvent(string memory _eventType) external;
    function unsubscribeFromEvent(string memory _eventType) external;

    // Utility functions
    function getLogCount() external view returns (uint256);
    function getEmergencyLogCount() external view returns (uint256);
    function isEmergencyMode() external view returns (bool);

    // State variables
    function owner() external view returns (address);
    function logCount() external view returns (uint256);
    function emergencyMode() external view returns (bool);
    function emergencyLogCount() external view returns (uint256);
    function authorizedLoggers(address) external view returns (bool);
    function eventSubscribers(address) external view returns (bool);
    function logs(bytes32) external view returns (
        uint256 id,
        uint256 timestamp,
        address actor,
        string memory eventType,
        bytes32 dataHash,
        string memory metadata,
        uint256 tenantId,
        uint8 severity,
        bool verified,
        bool archived
    );
}
