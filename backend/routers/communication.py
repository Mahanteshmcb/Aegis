"""
Aegis Backend - Communication Router

Provides endpoints for communication network health, emergency broadcast,
and offline message queue management.
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


class CommNetworkCreateRequest(BaseModel):
    name: str
    protocol: str = Field(..., description="Communication protocol such as grpc, mqtt, mesh, lte, satellite")
    secure: bool = True
    node_count: Optional[int] = 1
    is_offline_ready: bool = False
    metadata: Optional[Dict[str, Any]] = {}


class CommNetworkResponse(BaseModel):
    id: int
    name: str
    protocol: str
    secure: bool
    status: str
    signal_strength: Optional[float]
    latency_ms: Optional[float]
    bandwidth_mbps: Optional[float]
    node_count: int
    is_offline_ready: bool
    network_metadata: Dict[str, Any]
    last_checked: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class EmergencyBroadcastRequest(BaseModel):
    message: str
    priority: str = Field("high", description="Broadcast priority: high, medium, low")
    broadcast_type: str = Field("all", description="Broadcast target type: all, zones, staff")
    target_zones: Optional[List[str]] = []
    target_groups: Optional[List[str]] = []


class EmergencyBroadcastResponse(BaseModel):
    id: int
    message: str
    priority: str
    broadcast_type: str
    target_zones: List[str]
    target_groups: List[str]
    status: str
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class OfflineMessageRequest(BaseModel):
    destination: str
    payload: Dict[str, Any] = {}
    priority: str = Field("normal", description="Message priority: normal, high, low")
    metadata: Optional[Dict[str, Any]] = {}


class OfflineQueueItemResponse(BaseModel):
    id: int
    destination: str
    payload: Dict[str, Any]
    status: str
    priority: str
    queued_at: datetime
    delivered_at: Optional[datetime]
    message_metadata: Dict[str, Any]

    class Config:
        orm_mode = True
        from_attributes = True


class CommunicationStatusResponse(BaseModel):
    total_networks: int
    active_networks: int
    degraded_networks: int
    offline_networks: int
    secure_networks: int
    offline_ready: bool
    queued_messages: int
    recent_broadcasts: List[EmergencyBroadcastResponse]
    networks: List[CommNetworkResponse]

    class Config:
        orm_mode = True
        from_attributes = True


@router.get("/status", response_model=CommunicationStatusResponse)
async def communication_status(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    networks = db.query(models_db.CommunicationNetwork).filter(models_db.CommunicationNetwork.tenant_id == tenant_id).all()
    broadcasts = (
        db.query(models_db.EmergencyBroadcast)
        .filter(models_db.EmergencyBroadcast.tenant_id == tenant_id)
        .order_by(models_db.EmergencyBroadcast.created_at.desc())
        .limit(5)
        .all()
    )
    queued_messages = (
        db.query(models_db.OfflineMessageQueue)
        .filter(models_db.OfflineMessageQueue.tenant_id == tenant_id)
        .filter(models_db.OfflineMessageQueue.status == "queued")
        .count()
    )

    active_networks = sum(1 for network in networks if network.status == "connected")
    degraded_networks = sum(1 for network in networks if network.status == "degraded")
    offline_networks = sum(1 for network in networks if network.status == "offline")
    secure_networks = sum(1 for network in networks if network.secure)
    offline_ready = queued_messages > 0 or any(network.is_offline_ready or network.status != "connected" for network in networks)

    return CommunicationStatusResponse(
        total_networks=len(networks),
        active_networks=active_networks,
        degraded_networks=degraded_networks,
        offline_networks=offline_networks,
        secure_networks=secure_networks,
        offline_ready=offline_ready,
        queued_messages=queued_messages,
        recent_broadcasts=[EmergencyBroadcastResponse.from_orm(broadcast) for broadcast in broadcasts],
        networks=[CommNetworkResponse.from_orm(network) for network in networks],
    )


@router.post("/networks/register", response_model=CommNetworkResponse)
async def register_communication_network(request: CommNetworkCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    network = models_db.CommunicationNetwork(
        tenant_id=tenant_id,
        name=request.name,
        protocol=request.protocol,
        secure=request.secure,
        status="connected",
        signal_strength=100.0,
        latency_ms=10.0,
        bandwidth_mbps=100.0,
        node_count=request.node_count or 1,
        is_offline_ready=request.is_offline_ready,
        network_metadata=request.metadata or {},
        last_checked=datetime.utcnow(),
    )
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


@router.get("/networks", response_model=List[CommNetworkResponse])
async def list_communication_networks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    networks = db.query(models_db.CommunicationNetwork).filter(models_db.CommunicationNetwork.tenant_id == tenant_id).all()
    return networks


@router.post("/broadcast/emergency", response_model=EmergencyBroadcastResponse)
async def emergency_broadcast(request: EmergencyBroadcastRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    active_networks = db.query(models_db.CommunicationNetwork).filter(
        models_db.CommunicationNetwork.tenant_id == tenant_id,
        models_db.CommunicationNetwork.status == "connected"
    ).count()
    broadcast = models_db.EmergencyBroadcast(
        tenant_id=tenant_id,
        message=request.message,
        priority=request.priority,
        broadcast_type=request.broadcast_type,
        target_zones=request.target_zones or [],
        target_groups=request.target_groups or [],
        status="sent" if active_networks > 0 else "queued",
        sent_at=datetime.utcnow() if active_networks > 0 else None,
    )
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    return broadcast


@router.post("/offline/queue", response_model=OfflineQueueItemResponse)
async def queue_offline_message(request: OfflineMessageRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    message = models_db.OfflineMessageQueue(
        tenant_id=tenant_id,
        destination=request.destination,
        payload=request.payload or {},
        status="queued",
        priority=request.priority,
        message_metadata=request.metadata or {},
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/offline/queue", response_model=List[OfflineQueueItemResponse])
async def list_offline_messages(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    messages = (
        db.query(models_db.OfflineMessageQueue)
        .filter(models_db.OfflineMessageQueue.tenant_id == tenant_id)
        .order_by(models_db.OfflineMessageQueue.queued_at.desc())
        .all()
    )
    return messages
