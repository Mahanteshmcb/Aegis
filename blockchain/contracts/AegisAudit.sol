// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AegisAudit
 * @dev Enhanced immutable audit logging contract for the AEGIS IoT Platform
 * Features advanced event logging, batch operations, and compliance reporting
 */
contract AegisAudit {
    /**
     * @dev Represents a single audit log entry with enhanced metadata
     */
    struct LogEntry {
        uint256 id;
        uint256 timestamp;
        address actor;
        string eventType;
        bytes32 dataHash;
        string metadata;
        uint256 tenantId;
        uint8 severity;        // 0=INFO, 1=WARNING, 2=ERROR, 3=CRITICAL
        bool verified;
        bool archived;
    }

    /**
     * @dev Batch log entry for efficient bulk operations
     */
    struct BatchLogEntry {
        string eventType;
        bytes32 dataHash;
        string metadata;
        uint8 severity;
    }

    // ==================== CONSTANTS ====================
    uint8 constant SEVERITY_INFO = 0;
    uint8 constant SEVERITY_WARNING = 1;
    uint8 constant SEVERITY_ERROR = 2;
    uint8 constant SEVERITY_CRITICAL = 3;

    // Common event types for IoT operations
    string constant EVENT_DEVICE_ACTIVATED = "DEVICE_ACTIVATED";
    string constant EVENT_DEVICE_DEACTIVATED = "DEVICE_DEACTIVATED";
    string constant EVENT_SENSOR_DATA = "SENSOR_DATA";
    string constant EVENT_ACTUATOR_CONTROL = "ACTUATOR_CONTROL";
    string constant EVENT_SECURITY_ALERT = "SECURITY_ALERT";
    string constant EVENT_MAINTENANCE = "MAINTENANCE";
    string constant EVENT_COMPLIANCE_CHECK = "COMPLIANCE_CHECK";
    string constant EVENT_USER_ACCESS = "USER_ACCESS";
    string constant EVENT_SYSTEM_CONFIG = "SYSTEM_CONFIG";
    string constant EVENT_EMERGENCY = "EMERGENCY";

    // ==================== STATE VARIABLES ====================
    address public owner;
    uint256 public logCount = 0;

    mapping(bytes32 => LogEntry) public logs;
    bytes32[] public logIds;
    mapping(uint256 => bytes32[]) public tenantLogs;
    mapping(address => bool) public authorizedLoggers;

    // Enhanced query mappings
    mapping(string => bytes32[]) public eventTypeLogs;
    mapping(address => bytes32[]) public actorLogs;
    mapping(uint8 => bytes32[]) public severityLogs;
    mapping(uint256 => bytes32[]) public timeRangeLogs; // timestamp buckets

    // Emergency logging state
    bool public emergencyMode = false;
    uint256 public emergencyLogCount = 0;

    // Event subscription system
    mapping(address => bool) public eventSubscribers;
    mapping(string => address[]) public eventSubscriptions;

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

    // ==================== MODIFIERS ====================
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == owner || authorizedLoggers[msg.sender],
            "Not authorized to log"
        );
        _;
    }

    modifier logExists(bytes32 _logId) {
        require(logs[_logId].timestamp != 0, "Log entry does not exist");
        _;
    }

    // ==================== CONSTRUCTOR ====================
    constructor() {
        owner = msg.sender;
        authorizedLoggers[msg.sender] = true;
    }

    // ==================== OWNER FUNCTIONS ====================
    function addAuthorizedLogger(address _account) external onlyOwner {
        require(_account != address(0), "Invalid address");
        require(!authorizedLoggers[_account], "Already authorized");
        authorizedLoggers[_account] = true;
        emit AuthorizerAdded(_account);
    }

    function removeAuthorizedLogger(address _account) external onlyOwner {
        require(authorizedLoggers[_account], "Not authorized");
        require(_account != owner, "Cannot remove owner");
        authorizedLoggers[_account] = false;
        emit AuthorizerRemoved(_account);
    }

    function transferOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "Invalid address");
        owner = _newOwner;
        authorizedLoggers[_newOwner] = true;
    }

    function setEmergencyMode(bool _activate) external onlyOwner {
        emergencyMode = _activate;
        emit EmergencyModeChanged(_activate, msg.sender);
    }

    // ==================== LOGGING FUNCTIONS ====================
    /**
     * @dev Internal function to create a log entry with severity level
     */
    function _createLogInternal(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId,
        uint8 _severity
    ) internal returns (bytes32) {
        require(bytes(_eventType).length > 0, "Event type required");
        require(_tenantId > 0, "Valid tenant ID required");
        require(_severity <= SEVERITY_CRITICAL, "Invalid severity level");

        bytes32 logId = keccak256(
            abi.encodePacked(
                msg.sender,
                block.timestamp,
                block.number,
                logCount
            )
        );

        LogEntry memory entry = LogEntry({
            id: logCount,
            timestamp: block.timestamp,
            actor: msg.sender,
            eventType: _eventType,
            dataHash: _dataHash,
            metadata: _metadata,
            tenantId: _tenantId,
            severity: _severity,
            verified: true,
            archived: false
        });

        logs[logId] = entry;
        logIds.push(logId);
        tenantLogs[_tenantId].push(logId);
        eventTypeLogs[_eventType].push(logId);
        actorLogs[msg.sender].push(logId);
        severityLogs[_severity].push(logId);

        uint256 timeBucket = block.timestamp / 3600;
        timeRangeLogs[timeBucket].push(logId);

        logCount++;

        emit LogCreated(logId, _tenantId, msg.sender, _eventType, _severity, block.timestamp);
        _notifySubscribers(_eventType, logId);

        return logId;
    }

    /**
     * @dev Creates a new audit log entry with severity level
     */
    function createLog(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId,
        uint8 _severity
    ) external onlyAuthorized returns (bytes32) {
        return _createLogInternal(_eventType, _dataHash, _metadata, _tenantId, _severity);
    }

    /**
     * @dev Creates a log with INFO severity (overload for backward compatibility)
     */
    function createLog(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId
    ) external onlyAuthorized returns (bytes32) {
        return _createLogInternal(_eventType, _dataHash, _metadata, _tenantId, SEVERITY_INFO);
    }

    /**
     * @dev Creates an emergency log entry with CRITICAL severity
     */
    function emergencyLog(
        string memory _eventType,
        bytes32 _dataHash,
        string memory _metadata,
        uint256 _tenantId
    ) external onlyAuthorized returns (bytes32) {
        bytes32 logId = _createLogInternal(_eventType, _dataHash, _metadata, _tenantId, SEVERITY_CRITICAL);
        emergencyLogCount++;
        emit EmergencyLogCreated(logId, _tenantId, _eventType, block.timestamp);
        return logId;
    }

    /**
     * @dev Creates multiple audit log entries in a single transaction
     */
    function batchCreateLogs(
        BatchLogEntry[] memory _entries,
        uint256 _tenantId
    ) external onlyAuthorized returns (bytes32[] memory) {
        require(_entries.length > 0, "At least one entry required");
        require(_entries.length <= 50, "Maximum 50 entries per batch");
        require(_tenantId > 0, "Valid tenant ID required");

        bytes32[] memory batchLogIds = new bytes32[](_entries.length);
        uint256 currentTime = block.timestamp;
        uint256 timeBucket = currentTime / 3600;

        for (uint256 i = 0; i < _entries.length; i++) {
            BatchLogEntry memory entry = _entries[i];
            require(bytes(entry.eventType).length > 0, "Event type required");
            require(entry.severity <= SEVERITY_CRITICAL, "Invalid severity level");

            bytes32 logId = keccak256(
                abi.encodePacked(
                    msg.sender,
                    currentTime,
                    block.number,
                    logCount,
                    i
                )
            );

            LogEntry memory logEntry = LogEntry({
                id: logCount,
                timestamp: currentTime,
                actor: msg.sender,
                eventType: entry.eventType,
                dataHash: entry.dataHash,
                metadata: entry.metadata,
                tenantId: _tenantId,
                severity: entry.severity,
                verified: true,
                archived: false
            });

            logs[logId] = logEntry;
            batchLogIds[i] = logId;
            logIds.push(logId);
            tenantLogs[_tenantId].push(logId);
            eventTypeLogs[entry.eventType].push(logId);
            actorLogs[msg.sender].push(logId);
            severityLogs[entry.severity].push(logId);
            timeRangeLogs[timeBucket].push(logId);

            logCount++;
            _notifySubscribers(entry.eventType, logId);
        }

        emit BatchLogsCreated(batchLogIds, _tenantId, msg.sender, _entries.length, currentTime);
        return batchLogIds;
    }

    // ==================== QUERY FUNCTIONS ====================
    function getLog(bytes32 _logId)
        external
        view
        logExists(_logId)
        returns (LogEntry memory)
    {
        return logs[_logId];
    }

    function getTenantLogs(uint256 _tenantId)
        external
        view
        returns (bytes32[] memory)
    {
        return tenantLogs[_tenantId];
    }

    function getTenantLogCount(uint256 _tenantId)
        external
        view
        returns (uint256)
    {
        return tenantLogs[_tenantId].length;
    }

    function verifyLog(bytes32 _logId, bytes32 _expectedHash)
        external
        logExists(_logId)
        returns (bool)
    {
        LogEntry memory entry = logs[_logId];
        bool isValid = entry.dataHash == _expectedHash;

        if (isValid) {
            logs[_logId].verified = true;
        }

        emit LogVerified(_logId, isValid);
        return isValid;
    }

    function getLogCount() external view returns (uint256) {
        return logCount;
    }

    function getAllLogs() external view returns (bytes32[] memory) {
        return logIds;
    }

    // ==================== ENHANCED QUERY FUNCTIONS ====================
    function getLogsByEventType(string memory _eventType)
        external
        view
        returns (bytes32[] memory)
    {
        return eventTypeLogs[_eventType];
    }

    function getLogsByActor(address _actor)
        external
        view
        returns (bytes32[] memory)
    {
        return actorLogs[_actor];
    }

    function getLogsBySeverity(uint8 _severity)
        external
        view
        returns (bytes32[] memory)
    {
        require(_severity <= SEVERITY_CRITICAL, "Invalid severity level");
        return severityLogs[_severity];
    }

    function getRecentLogs(uint256 _count)
        external
        view
        returns (bytes32[] memory)
    {
        require(_count > 0 && _count <= 100, "Count must be between 1 and 100");

        uint256 totalLogs = logIds.length;
        uint256 startIndex = totalLogs > _count ? totalLogs - _count : 0;
        uint256 resultCount = totalLogs - startIndex;

        bytes32[] memory recentLogs = new bytes32[](resultCount);
        for (uint256 i = 0; i < resultCount; i++) {
            recentLogs[i] = logIds[startIndex + i];
        }

        return recentLogs;
    }

    function getLogsByTimeRange(uint256 _startTime, uint256 _endTime)
        external
        view
        returns (bytes32[] memory)
    {
        require(_startTime <= _endTime, "Invalid time range");

        uint256 startBucket = _startTime / 3600;
        uint256 endBucket = _endTime / 3600;
        uint256 estimatedSize = 0;

        for (uint256 bucket = startBucket; bucket <= endBucket; bucket++) {
            estimatedSize += timeRangeLogs[bucket].length;
        }

        bytes32[] memory result = new bytes32[](estimatedSize);
        uint256 resultIndex = 0;

        for (uint256 bucket = startBucket; bucket <= endBucket; bucket++) {
            bytes32[] memory bucketLogs = timeRangeLogs[bucket];
            for (uint256 i = 0; i < bucketLogs.length; i++) {
                bytes32 logId = bucketLogs[i];
                if (logs[logId].timestamp >= _startTime && logs[logId].timestamp <= _endTime) {
                    if (resultIndex < result.length) {
                        result[resultIndex] = logId;
                        resultIndex++;
                    }
                }
            }
        }

        assembly {
            mstore(result, resultIndex)
        }

        return result;
    }

    // ==================== COMPLIANCE REPORTING ====================
    function getComplianceSummary(uint256 _tenantId)
        external
        view
        returns (
            uint256 totalLogs,
            uint256 verifiedLogs,
            uint256 criticalLogs,
            uint256 emergencyLogs
        )
    {
        bytes32[] memory tenantLogIds = tenantLogs[_tenantId];
        totalLogs = tenantLogIds.length;

        for (uint256 i = 0; i < tenantLogIds.length; i++) {
            LogEntry memory entry = logs[tenantLogIds[i]];
            if (entry.verified) {
                verifiedLogs++;
            }
            if (entry.severity == SEVERITY_CRITICAL) {
                criticalLogs++;
            }
            if (keccak256(bytes(entry.eventType)) == keccak256(bytes(EVENT_EMERGENCY))) {
                emergencyLogs++;
            }
        }
    }

    function getAuditStatistics()
        external
        view
        returns (
            uint256 totalLogs,
            uint256 totalTenants,
            uint256 emergencyCount,
            uint256 avgSeverity
        )
    {
        totalLogs = logCount;
        emergencyCount = emergencyLogCount;

        uint256[] memory tenantList = new uint256[](totalLogs);
        uint256 tenantCount = 0;

        for (uint256 i = 0; i < totalLogs; i++) {
            uint256 tenantId = logs[logIds[i]].tenantId;
            bool exists = false;
            for (uint256 j = 0; j < tenantCount; j++) {
                if (tenantList[j] == tenantId) {
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                tenantList[tenantCount] = tenantId;
                tenantCount++;
            }
        }

        totalTenants = tenantCount;

        uint256 totalSeverity = 0;
        for (uint256 i = 0; i < totalLogs; i++) {
            totalSeverity += logs[logIds[i]].severity;
        }
        avgSeverity = totalLogs > 0 ? totalSeverity / totalLogs : 0;
    }

    // ==================== EVENT SUBSCRIPTION ====================
    function subscribeToEvent(string memory _eventType) external {
        require(!eventSubscribers[msg.sender], "Already subscribed");
        eventSubscribers[msg.sender] = true;
        eventSubscriptions[_eventType].push(msg.sender);
        emit EventSubscribed(msg.sender, _eventType);
    }

    function unsubscribeFromEvent(string memory _eventType) external {
        require(eventSubscribers[msg.sender], "Not subscribed");

        address[] storage subscribers = eventSubscriptions[_eventType];
        for (uint256 i = 0; i < subscribers.length; i++) {
            if (subscribers[i] == msg.sender) {
                subscribers[i] = subscribers[subscribers.length - 1];
                subscribers.pop();
                break;
            }
        }

        bool stillSubscribed = false;
        string[10] memory eventTypes = [
            EVENT_DEVICE_ACTIVATED, EVENT_DEVICE_DEACTIVATED, EVENT_SENSOR_DATA,
            EVENT_ACTUATOR_CONTROL, EVENT_SECURITY_ALERT, EVENT_MAINTENANCE,
            EVENT_COMPLIANCE_CHECK, EVENT_USER_ACCESS, EVENT_SYSTEM_CONFIG, EVENT_EMERGENCY
        ];

        for (uint256 i = 0; i < eventTypes.length; i++) {
            address[] memory subs = eventSubscriptions[eventTypes[i]];
            for (uint256 j = 0; j < subs.length; j++) {
                if (subs[j] == msg.sender) {
                    stillSubscribed = true;
                    break;
                }
            }
            if (stillSubscribed) break;
        }

        if (!stillSubscribed) {
            eventSubscribers[msg.sender] = false;
        }

        emit EventUnsubscribed(msg.sender, _eventType);
    }

    function _notifySubscribers(string memory _eventType, bytes32 _logId) internal {
        address[] memory subscribers = eventSubscriptions[_eventType];
        for (uint256 i = 0; i < subscribers.length; i++) {
            // Notification hook for subscribers
        }
    }

    // ==================== UTILITY FUNCTIONS ====================
    function archiveLog(bytes32 _logId) external onlyOwner logExists(_logId) {
        logs[_logId].archived = true;
    }

    function getEmergencyLogCount() external view returns (uint256) {
        return emergencyLogCount;
    }

    function isEmergencyMode() external view returns (bool) {
        return emergencyMode;
    }
}