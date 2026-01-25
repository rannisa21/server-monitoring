import time
from app import db
from app.models.server import Server, Component
from app.models.metric import Metric
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

def wib_now():
    """Return current time in WIB (UTC+7) as naive datetime."""
    utc_now = datetime.now(timezone.utc)
    wib_time = utc_now + timedelta(hours=7)
    return wib_time.replace(tzinfo=None)  # Remove timezone info for PostgreSQL
from flask import current_app
from pysnmp.hlapi import (
    getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity,
    UsmUserData, usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol, usmDESPrivProtocol, usmAesCfb128Protocol
)
import logging

logger = logging.getLogger(__name__)

# SNMP value classification per brand/component
SNMP_CLASSIFICATION = {
    'HPE': {
        'fan': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'PSU': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'harddisk': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'suhu': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if float(v) < 50 else ('Warning' if float(v) < 60 else 'Critical')),
    },
    'Dell': {
        'fan': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'PSU': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'harddisk': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'suhu': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if float(v) < 55 else ('Warning' if float(v) < 65 else 'Critical')),
    },
    'supermicro': {
        'fan': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'PSU': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'harddisk': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'suhu': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if float(v) < 50 else ('Warning' if float(v) < 60 else 'Critical')),
    },
    'custom': {
        'fan': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'PSU': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'harddisk': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
        'suhu': lambda v: 'Unknown' if v is None or str(v).strip() == '' else
            ('OK' if str(v).lower() in ['ok', 'good', '1', '2']
             else ('Warning' if str(v).lower() in ['warning', 'degraded', '3']
                   else 'Critical')),
    }
}




def snmp_get(server, component):
    """Perform SNMP GET operation for a component on a server."""
    logger.debug(f"SNMP GET: server={server.name} ip={server.ip} oid={component.oid} v={server.snmp_version}")
    try:
        if server.snmp_version == 'v2c':
            if not server.community:
                logger.error(f"SNMP v2c requires community string for server {server.name}")
                return None
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(server.community, mpModel=1),
                UdpTransportTarget((server.ip, 161), timeout=2, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(component.oid))
            )
        else:  # v3
            if not server.snmp_auth_user or not server.snmp_auth_pass:
                logger.error(f"SNMP v3 requires auth credentials for server {server.name}")
                return None
            
            auth_proto = usmHMACMD5AuthProtocol if server.snmp_auth_proto == 'MD5' else usmHMACSHAAuthProtocol
            priv_proto = usmDESPrivProtocol if server.snmp_priv_proto == 'DES' else usmAesCfb128Protocol
            
            iterator = getCmd(
                SnmpEngine(),
                UsmUserData(
                    server.snmp_auth_user,
                    server.snmp_auth_pass,
                    server.snmp_priv_pass,
                    authProtocol=auth_proto,
                    privProtocol=priv_proto
                ),
                UdpTransportTarget((server.ip, 161), timeout=2, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(component.oid))
            )
        
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        
        if errorIndication:
            logger.warning(f"SNMP Error Indication for {server.name}/{component.name}: {errorIndication}")
            return None
        if errorStatus:
            logger.warning(f"SNMP Error Status for {server.name}/{component.name}: {errorStatus.prettyPrint()} at {errorIndex}")
            return None
        
        for varBind in varBinds:
            value = str(varBind[1])
            logger.debug(f"SNMP Result for {server.name}/{component.name}: {value}")
            return value
            
    except Exception as e:
        logger.error(f"SNMP Exception for {server.name}/{component.name}: {e}", exc_info=True)
        return None
    
    return None


def classify_value(server, component, value):
    """Classify SNMP value based on brand and component category."""
    try:
        brand_classifiers = SNMP_CLASSIFICATION.get(server.brand, SNMP_CLASSIFICATION['custom'])
        classifier = brand_classifiers.get(component.category, lambda v: 'OK')
        return classifier(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Classification error for {server.name}/{component.name}: {e}")
        return 'Critical'


def poll_all():
    """Poll all servers and components for SNMP metrics."""
    logger.info("Starting SNMP polling for all servers/components")
    
    poll_start = datetime.utcnow()
    success_count = 0
    error_count = 0
    
    try:
        servers = Server.query.all()
        
        if not servers:
            logger.info("No servers configured for polling")
            return
        
        for server in servers:
            if not server.components:
                logger.debug(f"Server {server.name} has no components configured")
                continue
            
            for component in server.components:
                try:
                    value = snmp_get(server, component)
                    
                    if value is None:
                        status = 'Critical'
                        value = 'N/A'
                        error_count += 1
                    else:
                        status = classify_value(server, component, value)
                        success_count += 1
                    
                    metric = Metric(
                        server_id=server.id,
                        component_id=component.id,
                        oid=component.oid,
                        value=value,
                        status=status,
                        brand=server.brand,
                        component_name=component.name,
                        server_name=server.name,
                        server_ip=server.ip,
                        category=component.category,
                        timestamp=wib_now()
                    )
                    db.session.add(metric)
                    
                except Exception as e:
                    logger.error(f"Error polling {server.name}/{component.name}: {e}", exc_info=True)
                    error_count += 1
        
        db.session.commit()
        
        poll_duration = (datetime.utcnow() - poll_start).total_seconds()
        logger.info(f"SNMP polling completed: {success_count} success, {error_count} errors, duration: {poll_duration:.2f}s")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Critical error during SNMP polling: {e}", exc_info=True)


def poll_all_with_context(app):
    """Run poll_all within application context."""
    try:
        with app.app_context():
            poll_all()
    except Exception as e:
        logger.error(f"Error running poll_all_with_context: {e}", exc_info=True)


def start_scheduler(app):
    """Start the background scheduler for periodic SNMP polling."""
    try:
        poll_interval = app.config.get('SNMP_POLL_INTERVAL_MINUTES', 5)
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=lambda: poll_all_with_context(app),
            trigger="interval",
            minutes=poll_interval,
            id='snmp_polling',
            replace_existing=True
        )
        scheduler.start()
        
        app.scheduler = scheduler
        logger.info(f"SNMP polling scheduler started with {poll_interval} minute interval")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
