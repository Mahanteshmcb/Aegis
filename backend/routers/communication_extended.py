"""
Aegis Backend - Extended Communication Router

Provides comprehensive communication infrastructure for:
1. Robot fleet communication channels
2. IoT device/sensor communication channels
3. Zone-to-zone communication channels
4. Inter-server communication channels
5. Vryndara AI service communication channels
6. Cross-layer communication orchestration
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend import models_db

router = APIRouter(prefix="/api/v1/communication", tags=["Communication"])
logger = logging.getLogger(__name__)


# ==================== RESPONSE MODELS ====================

class RobotChannelResponse(BaseModel):
    id: int
    channel_name: str
    protocol: str
    status: str
    robot_ids: List[str]
    active_robots: int
    signal_strength: float
    latency_ms: float
    bandwidth_mbps: float
    last_heartbeat: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class DeviceChannelResponse(BaseModel):
    id: int
    channel_name: str
    protocol: str
    status: str
    device_ids: List[str]
    active_devices: int
    signal_strength: float
    latency_ms: float
    bandwidth_mbps: float
    mesh_topology: str
    last_sync: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class ZoneChannelResponse(BaseModel):
    id: int
    zone_id: int
    channel_name: str
    protocol: str
    status: str
    connected_zones: List[int]
    active_connections: int
    signal_strength: float
    latency_ms: float
    bandwidth_mbps: float
    message_throughput: int
    last_message: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class ServerChannelResponse(BaseModel):
    id: int
    server_id: str
    server_name: str
    protocol: str
    status: str
    peer_servers: List[str]
    active_connections: int
    health_score: float
    latency_ms: float
    bandwidth_mbps: float
    is_primary: bool
    last_health_check: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class VryndaraChannelResponse(BaseModel):
    id: int
    service_endpoint: str
    protocol: str
    status: str
    service_version: Optional[str]
    ai_model_version: Optional[str]
    latency_ms: float
    current_requests: int
    max_concurrent_requests: int
    successful_requests: int
    failed_requests: int
    ai_health_score: float
    last_request: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class CommunicationOrchestrationResponse(BaseModel):
    id: int
    orchestration_id: str
    orchestration_type: str
    source_type: str
    target_type: str
    source_id: str
    target_id: str
    status: str
    routing_priority: int
    message_count: int
    failure_count: int
    last_message_timestamp: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class FullCommunicationStatusResponse(BaseModel):
    timestamp: datetime
    robot_channels: List[RobotChannelResponse]
    device_channels: List[DeviceChannelResponse]
    zone_channels: List[ZoneChannelResponse]
    server_channels: List[ServerChannelResponse]
    vryndara_channel: Optional[VryndaraChannelResponse]
    orchestrations: List[CommunicationOrchestrationResponse]
    overall_health: float
    total_message_throughput: int


# ==================== REQUEST MODELS ====================

class RobotChannelCreateRequest(BaseModel):
    channel_name: str
    protocol: str = Field("grpc", description="grpc, mqtt, websocket")
    robot_ids: Optional[List[str]] = []


class DeviceChannelCreateRequest(BaseModel):
    channel_name: str
    protocol: str = Field("mqtt", description="mqtt, coap, zigbee, lte")
    device_ids: Optional[List[str]] = []
    mesh_topology: str = Field("star", description="star, mesh, hybrid")


class ZoneChannelCreateRequest(BaseModel):
    zone_id: int
    channel_name: str
    protocol: str = Field("mqtt", description="mqtt, grpc, rest")
    connected_zones: Optional[List[int]] = []


class ServerChannelCreateRequest(BaseModel):
    server_id: str
    server_name: str
    protocol: str = Field("grpc", description="grpc, rest, websocket")
    peer_servers: Optional[List[str]] = []
    is_primary: bool = False


class VryndaraChannelConfigRequest(BaseModel):
    service_endpoint: str
    protocol: str = Field("grpc", description="grpc, rest, websocket")
    request_timeout_ms: int = 5000
    max_concurrent_requests: int = 100


class OrchestrationCreateRequest(BaseModel):
    orchestration_type: str
    source_type: str  # robot, device, zone, server, vryndara
    target_type: str
    source_id: str
    target_id: str
    routing_priority: int = 0


# ==================== ROBOT COMMUNICATION ENDPOINTS ====================

@router.post("/robots/channels", response_model=RobotChannelResponse)
async def create_robot_channel(
    request: RobotChannelCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new robot fleet communication channel."""
    tenant_id = current_user["tenant_id"]
    channel = models_db.RobotCommunicationChannel(
        tenant_id=tenant_id,
        channel_name=request.channel_name,
        protocol=request.protocol,
        status="connected",
        robot_ids=request.robot_ids or [],
        active_robots=len(request.robot_ids or []),
        signal_strength=100.0,
        latency_ms=10.0,
        bandwidth_mbps=100.0,
        last_heartbeat=datetime.utcnow(),
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    logger.info(f"Created robot channel {request.channel_name} for tenant {tenant_id}")
    return channel


@router.get("/robots/channels", response_model=List[RobotChannelResponse])
async def list_robot_channels(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all robot communication channels for the tenant."""
    tenant_id = current_user["tenant_id"]
    channels = db.query(models_db.RobotCommunicationChannel).filter(
        models_db.RobotCommunicationChannel.tenant_id == tenant_id
    ).all()
    return channels


@router.post("/robots/channels/{channel_id}/heartbeat", response_model=RobotChannelResponse)
async def robot_channel_heartbeat(
    channel_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update robot channel heartbeat and status."""
    tenant_id = current_user["tenant_id"]
    channel = db.query(models_db.RobotCommunicationChannel).filter(
        models_db.RobotCommunicationChannel.id == channel_id,
        models_db.RobotCommunicationChannel.tenant_id == tenant_id,
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    channel.last_heartbeat = datetime.utcnow()
    channel.status = "connected"
    db.commit()
    db.refresh(channel)
    return channel


# ==================== DEVICE COMMUNICATION ENDPOINTS ====================

@router.post("/devices/channels", response_model=DeviceChannelResponse)
async def create_device_channel(
    request: DeviceChannelCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new IoT device communication channel."""
    tenant_id = current_user["tenant_id"]
    channel = models_db.DeviceCommunicationChannel(
        tenant_id=tenant_id,
        channel_name=request.channel_name,
        protocol=request.protocol,
        status="connected",
        device_ids=request.device_ids or [],
        active_devices=len(request.device_ids or []),
        signal_strength=100.0,
        latency_ms=50.0,
        bandwidth_mbps=10.0,
        mesh_topology=request.mesh_topology,
        last_sync=datetime.utcnow(),
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    logger.info(f"Created device channel {request.channel_name} for tenant {tenant_id}")
    return channel


@router.get("/devices/channels", response_model=List[DeviceChannelResponse])
async def list_device_channels(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all device communication channels for the tenant."""
    tenant_id = current_user["tenant_id"]
    channels = db.query(models_db.DeviceCommunicationChannel).filter(
        models_db.DeviceCommunicationChannel.tenant_id == tenant_id
    ).all()
    return channels


@router.post("/devices/channels/{channel_id}/sync", response_model=DeviceChannelResponse)
async def device_channel_sync(
    channel_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Synchronize device channel and update last sync time."""
    tenant_id = current_user["tenant_id"]
    channel = db.query(models_db.DeviceCommunicationChannel).filter(
        models_db.DeviceCommunicationChannel.id == channel_id,
        models_db.DeviceCommunicationChannel.tenant_id == tenant_id,
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    channel.last_sync = datetime.utcnow()
    channel.status = "connected"
    db.commit()
    db.refresh(channel)
    return channel


# ==================== ZONE COMMUNICATION ENDPOINTS ====================

@router.post("/zones/channels", response_model=ZoneChannelResponse)
async def create_zone_channel(
    request: ZoneChannelCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new zone communication channel."""
    tenant_id = current_user["tenant_id"]
    
    # Verify zone exists
    zone = db.query(models_db.Zone).filter(
        models_db.Zone.id == request.zone_id,
        models_db.Zone.tenant_id == tenant_id,
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    channel = models_db.ZoneCommunicationChannel(
        tenant_id=tenant_id,
        zone_id=request.zone_id,
        channel_name=request.channel_name,
        protocol=request.protocol,
        status="connected",
        connected_zones=request.connected_zones or [],
        active_connections=len(request.connected_zones or []),
        signal_strength=100.0,
        latency_ms=20.0,
        bandwidth_mbps=50.0,
        message_throughput=0,
        last_message=datetime.utcnow(),
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    logger.info(f"Created zone channel for zone {request.zone_id} in tenant {tenant_id}")
    return channel


@router.get("/zones/channels", response_model=List[ZoneChannelResponse])
async def list_zone_channels(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all zone communication channels for the tenant."""
    tenant_id = current_user["tenant_id"]
    channels = db.query(models_db.ZoneCommunicationChannel).filter(
        models_db.ZoneCommunicationChannel.tenant_id == tenant_id
    ).all()
    return channels


@router.get("/zones/{zone_id}/channel", response_model=ZoneChannelResponse)
async def get_zone_channel(
    zone_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get communication channel for a specific zone."""
    tenant_id = current_user["tenant_id"]
    channel = db.query(models_db.ZoneCommunicationChannel).filter(
        models_db.ZoneCommunicationChannel.zone_id == zone_id,
        models_db.ZoneCommunicationChannel.tenant_id == tenant_id,
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Zone channel not found")
    return channel


# ==================== SERVER COMMUNICATION ENDPOINTS ====================

@router.post("/servers/channels", response_model=ServerChannelResponse)
async def register_server_channel(
    request: ServerChannelCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new server in the communication mesh."""
    tenant_id = current_user["tenant_id"]
    channel = models_db.ServerCommunicationChannel(
        tenant_id=tenant_id,
        server_id=request.server_id,
        server_name=request.server_name,
        protocol=request.protocol,
        status="healthy",
        peer_servers=request.peer_servers or [],
        active_connections=len(request.peer_servers or []),
        health_score=100.0,
        latency_ms=5.0,
        bandwidth_mbps=1000.0,
        is_primary=request.is_primary,
        last_health_check=datetime.utcnow(),
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    logger.info(f"Registered server {request.server_name} (ID: {request.server_id}) for tenant {tenant_id}")
    return channel


@router.get("/servers/channels", response_model=List[ServerChannelResponse])
async def list_server_channels(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all servers in the communication mesh."""
    tenant_id = current_user["tenant_id"]
    channels = db.query(models_db.ServerCommunicationChannel).filter(
        models_db.ServerCommunicationChannel.tenant_id == tenant_id
    ).order_by(models_db.ServerCommunicationChannel.is_primary.desc()).all()
    return channels


@router.post("/servers/{server_id}/health-check", response_model=ServerChannelResponse)
async def server_health_check(
    server_id: str,
    health_score: float = 100.0,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update server health check status."""
    tenant_id = current_user["tenant_id"]
    channel = db.query(models_db.ServerCommunicationChannel).filter(
        models_db.ServerCommunicationChannel.server_id == server_id,
        models_db.ServerCommunicationChannel.tenant_id == tenant_id,
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Server not found")
    
    channel.health_score = min(100.0, max(0.0, health_score))
    channel.status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
    channel.last_health_check = datetime.utcnow()
    db.commit()
    db.refresh(channel)
    return channel


# ==================== VRYNDARA COMMUNICATION ENDPOINTS ====================

@router.post("/vryndara/channel/configure", response_model=VryndaraChannelResponse)
async def configure_vryndara_channel(
    request: VryndaraChannelConfigRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Configure or update Vryndara AI service communication channel."""
    tenant_id = current_user["tenant_id"]
    
    # Check if Vryndara channel already exists
    existing = db.query(models_db.VryndaraCommunicationChannel).filter(
        models_db.VryndaraCommunicationChannel.tenant_id == tenant_id
    ).first()
    
    if existing:
        # Update existing channel
        existing.service_endpoint = request.service_endpoint
        existing.protocol = request.protocol
        existing.request_timeout_ms = request.request_timeout_ms
        existing.max_concurrent_requests = request.max_concurrent_requests
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated Vryndara channel for tenant {tenant_id}")
        return existing
    
    # Create new channel
    channel = models_db.VryndaraCommunicationChannel(
        tenant_id=tenant_id,
        service_endpoint=request.service_endpoint,
        protocol=request.protocol,
        status="connected",
        latency_ms=100.0,
        request_timeout_ms=request.request_timeout_ms,
        max_concurrent_requests=request.max_concurrent_requests,
        ai_health_score=100.0,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    logger.info(f"Created Vryndara channel for tenant {tenant_id}")
    return channel


@router.get("/vryndara/channel", response_model=Optional[VryndaraChannelResponse])
async def get_vryndara_channel(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get Vryndara AI service communication channel status."""
    tenant_id = current_user["tenant_id"]
    channel = db.query(models_db.VryndaraCommunicationChannel).filter(
        models_db.VryndaraCommunicationChannel.tenant_id == tenant_id
    ).first()
    return channel


@router.post("/vryndara/request", response_model=VryndaraChannelResponse)
async def record_vryndara_request(
    success: bool = True,
    latency_ms: Optional[float] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record Vryndara request and update statistics."""
    tenant_id = current_user["tenant_id"]
    channel = db.query(models_db.VryndaraCommunicationChannel).filter(
        models_db.VryndaraCommunicationChannel.tenant_id == tenant_id
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Vryndara channel not configured")
    
    channel.current_requests = max(0, channel.current_requests - 1)
    if success:
        channel.successful_requests += 1
    else:
        channel.failed_requests += 1
    channel.last_request = datetime.utcnow()
    if latency_ms:
        channel.latency_ms = latency_ms
    
    # Calculate health score
    total_requests = channel.successful_requests + channel.failed_requests
    if total_requests > 0:
        success_rate = channel.successful_requests / total_requests
        channel.ai_health_score = success_rate * 100.0
    
    db.commit()
    db.refresh(channel)
    return channel


# ==================== ORCHESTRATION ENDPOINTS ====================

@router.post("/orchestration/routes", response_model=CommunicationOrchestrationResponse)
async def create_orchestration_route(
    request: OrchestrationCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a cross-layer communication orchestration route."""
    tenant_id = current_user["tenant_id"]
    orchestration_id = f"{request.source_type}_{request.source_id}_to_{request.target_type}_{request.target_id}"
    
    route = models_db.CommunicationOrchestration(
        tenant_id=tenant_id,
        orchestration_id=orchestration_id,
        orchestration_type=request.orchestration_type,
        source_type=request.source_type,
        target_type=request.target_type,
        source_id=request.source_id,
        target_id=request.target_id,
        status="active",
        routing_priority=request.routing_priority,
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    logger.info(f"Created orchestration route {orchestration_id} for tenant {tenant_id}")
    return route


@router.get("/orchestration/routes", response_model=List[CommunicationOrchestrationResponse])
async def list_orchestration_routes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all active orchestration routes."""
    tenant_id = current_user["tenant_id"]
    routes = db.query(models_db.CommunicationOrchestration).filter(
        models_db.CommunicationOrchestration.tenant_id == tenant_id,
        models_db.CommunicationOrchestration.status == "active",
    ).order_by(models_db.CommunicationOrchestration.routing_priority.desc()).all()
    return routes


# ==================== UNIFIED STATUS ENDPOINTS ====================

@router.get("/full-status", response_model=FullCommunicationStatusResponse)
async def get_full_communication_status(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comprehensive communication infrastructure status across all layers."""
    tenant_id = current_user["tenant_id"]
    
    # Fetch all channel types
    robot_channels = db.query(models_db.RobotCommunicationChannel).filter(
        models_db.RobotCommunicationChannel.tenant_id == tenant_id
    ).all()
    
    device_channels = db.query(models_db.DeviceCommunicationChannel).filter(
        models_db.DeviceCommunicationChannel.tenant_id == tenant_id
    ).all()
    
    zone_channels = db.query(models_db.ZoneCommunicationChannel).filter(
        models_db.ZoneCommunicationChannel.tenant_id == tenant_id
    ).all()
    
    server_channels = db.query(models_db.ServerCommunicationChannel).filter(
        models_db.ServerCommunicationChannel.tenant_id == tenant_id
    ).all()
    
    vryndara_channel = db.query(models_db.VryndaraCommunicationChannel).filter(
        models_db.VryndaraCommunicationChannel.tenant_id == tenant_id
    ).first()
    
    orchestrations = db.query(models_db.CommunicationOrchestration).filter(
        models_db.CommunicationOrchestration.tenant_id == tenant_id,
        models_db.CommunicationOrchestration.status == "active",
    ).all()
    
    # Calculate overall health
    all_channels = robot_channels + device_channels + zone_channels + server_channels
    if vryndara_channel:
        all_channels.append(vryndara_channel)
    
    if all_channels:
        avg_health = sum(
            getattr(ch, "health_score", getattr(ch, "ai_health_score", 100.0))
            for ch in all_channels
        ) / len(all_channels)
    else:
        avg_health = 100.0
    
    # Calculate total message throughput
    total_throughput = sum(
        getattr(ch, "message_throughput", 0) for ch in zone_channels
    )
    
    return FullCommunicationStatusResponse(
        timestamp=datetime.utcnow(),
        robot_channels=[RobotChannelResponse.from_orm(ch) for ch in robot_channels],
        device_channels=[DeviceChannelResponse.from_orm(ch) for ch in device_channels],
        zone_channels=[ZoneChannelResponse.from_orm(ch) for ch in zone_channels],
        server_channels=[ServerChannelResponse.from_orm(ch) for ch in server_channels],
        vryndara_channel=VryndaraChannelResponse.from_orm(vryndara_channel) if vryndara_channel else None,
        orchestrations=[CommunicationOrchestrationResponse.from_orm(o) for o in orchestrations],
        overall_health=avg_health,
        total_message_throughput=total_throughput,
    )
