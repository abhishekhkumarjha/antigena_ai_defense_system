"""
Response Engine for Automated Threat Response
Handles automated response actions for detected anomalies
Part of Antigena-inspired Self-Learning AI Defense System
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseLevel(Enum):
    """Response severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResponseAction(Enum):
    """Types of response actions"""
    LOG_ONLY = "log_only"
    ALERT_SOC = "alert_soc"
    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    QUARANTINE_USER = "quarantine_user"
    BLOCK_PORT = "block_port"
    RATE_LIMIT = "rate_limit"
    ESCALATE = "escalate"

@dataclass
class ResponseRule:
    """Response rule configuration"""
    name: str
    condition: Dict[str, Any]
    actions: List[ResponseAction]
    level: ResponseLevel
    enabled: bool = True
    cooldown_minutes: int = 5

@dataclass
class ThreatEvent:
    """Threat event data structure"""
    timestamp: datetime
    anomaly_score: float
    features: List[float]
    source: Optional[str]
    ip_address: Optional[str] = None
    user_id: Optional[str] = None
    host_id: Optional[str] = None
    threat_type: Optional[str] = None

class ResponseEngine:
    """Automated response engine for threat mitigation"""
    
    def __init__(self, config_path: str = "config/response_config.json"):
        """
        Initialize response engine
        
        Args:
            config_path: Path to response configuration file
        """
        self.config_path = config_path
        self.rules = []
        self.action_history = []
        self.cooldown_tracker = {}
        self.email_config = None
        self.slack_webhook = None
        
        # Load configuration
        self.load_config()
        
        # Initialize default rules
        self.initialize_default_rules()
        
        logger.info("Response engine initialized")
    
    def load_config(self) -> None:
        """Load response configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                self.email_config = config.get('email', {})
                self.slack_webhook = config.get('slack_webhook')
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def initialize_default_rules(self) -> None:
        """Initialize default response rules"""
        default_rules = [
            ResponseRule(
                name="Low Severity Anomaly",
                condition={"min_score": 0.5, "max_score": 0.7},
                actions=[ResponseAction.LOG_ONLY, ResponseAction.ALERT_SOC],
                level=ResponseLevel.LOW,
                cooldown_minutes=10
            ),
            ResponseRule(
                name="Medium Severity Anomaly",
                condition={"min_score": 0.7, "max_score": 0.85},
                actions=[ResponseAction.LOG_ONLY, ResponseAction.ALERT_SOC, ResponseAction.RATE_LIMIT],
                level=ResponseLevel.MEDIUM,
                cooldown_minutes=5
            ),
            ResponseRule(
                name="High Severity Anomaly",
                condition={"min_score": 0.85, "max_score": 0.95},
                actions=[ResponseAction.LOG_ONLY, ResponseAction.ALERT_SOC, ResponseAction.BLOCK_IP, ResponseAction.ISOLATE_HOST],
                level=ResponseLevel.HIGH,
                cooldown_minutes=2
            ),
            ResponseRule(
                name="Critical Severity Anomaly",
                condition={"min_score": 0.95, "max_score": 1.0},
                actions=[ResponseAction.LOG_ONLY, ResponseAction.ALERT_SOC, ResponseAction.BLOCK_IP, 
                        ResponseAction.ISOLATE_HOST, ResponseAction.QUARANTINE_USER, ResponseAction.ESCALATE],
                level=ResponseLevel.CRITICAL,
                cooldown_minutes=1
            )
        ]
        
        self.rules.extend(default_rules)
        logger.info(f"Initialized {len(default_rules)} default response rules")
    
    def evaluate_threat(self, anomaly_score: float, features: List[float], 
                       source: str = None, **kwargs) -> Optional[ResponseRule]:
        """
        Evaluate threat and determine response rule
        
        Args:
            anomaly_score: Anomaly score (0-1)
            features: Feature vector
            source: Source of the data
            **kwargs: Additional threat context
            
        Returns:
            Matching response rule or None
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if self.is_in_cooldown(rule.name):
                continue
            
            # Check condition
            if self._evaluate_condition(rule.condition, anomaly_score, **kwargs):
                return rule
        
        return None
    
    def _evaluate_condition(self, condition: Dict[str, Any], anomaly_score: float, **kwargs) -> bool:
        """Evaluate rule condition"""
        min_score = condition.get('min_score', 0.0)
        max_score = condition.get('max_score', 1.0)
        
        score_match = min_score <= anomaly_score <= max_score
        
        # Add additional condition checks here
        # For example: IP reputation, user behavior, time of day, etc.
        
        return score_match
    
    def is_in_cooldown(self, rule_name: str) -> bool:
        """Check if rule is in cooldown period"""
        if rule_name not in self.cooldown_tracker:
            return False
        
        last_action = self.cooldown_tracker[rule_name]
        cooldown_end = last_action + timedelta(minutes=self.get_cooldown_minutes(rule_name))
        
        return datetime.now() < cooldown_end
    
    def get_cooldown_minutes(self, rule_name: str) -> int:
        """Get cooldown minutes for a rule"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule.cooldown_minutes
        return 5  # Default
    
    async def handle_anomaly(self, anomaly_score: float, features: List[float], 
                           source: str = None, **kwargs) -> Dict[str, Any]:
        """
        Handle detected anomaly
        
        Args:
            anomaly_score: Anomaly score (0-1)
            features: Feature vector
            source: Source of the data
            **kwargs: Additional context
            
        Returns:
            Response action results
        """
        # Create threat event
        threat_event = ThreatEvent(
            timestamp=datetime.now(),
            anomaly_score=anomaly_score,
            features=features,
            source=source,
            **kwargs
        )
        
        # Evaluate threat
        rule = self.evaluate_threat(anomaly_score, features, source, **kwargs)
        
        if rule is None:
            logger.info(f"No matching rule for anomaly score {anomaly_score:.3f}")
            return {"status": "no_action", "reason": "no_matching_rule"}
        
        logger.warning(f"🚨 Threat Detected - Score: {anomaly_score:.3f}, Level: {rule.level.value}")
        
        # Execute response actions
        results = await self.execute_actions(rule, threat_event)
        
        # Update cooldown
        self.cooldown_tracker[rule.name] = datetime.now()
        
        # Log action
        self.log_action(rule, threat_event, results)
        
        return {
            "status": "action_taken",
            "rule": rule.name,
            "level": rule.level.value,
            "actions": [action.value for action in rule.actions],
            "results": results
        }
    
    async def execute_actions(self, rule: ResponseRule, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Execute response actions for a threat"""
        results = {}
        
        for action in rule.actions:
            try:
                if action == ResponseAction.LOG_ONLY:
                    results[action.value] = self.action_log_only(threat_event)
                
                elif action == ResponseAction.ALERT_SOC:
                    results[action.value] = await self.action_alert_soc(threat_event, rule.level)
                
                elif action == ResponseAction.BLOCK_IP:
                    results[action.value] = self.action_block_ip(threat_event)
                
                elif action == ResponseAction.ISOLATE_HOST:
                    results[action.value] = self.action_isolate_host(threat_event)
                
                elif action == ResponseAction.QUARANTINE_USER:
                    results[action.value] = self.action_quarantine_user(threat_event)
                
                elif action == ResponseAction.RATE_LIMIT:
                    results[action.value] = self.action_rate_limit(threat_event)
                
                elif action == ResponseAction.ESCALATE:
                    results[action.value] = await self.action_escalate(threat_event)
                
                else:
                    results[action.value] = {"status": "unknown_action"}
                    
            except Exception as e:
                logger.error(f"Error executing action {action.value}: {e}")
                results[action.value] = {"status": "error", "error": str(e)}
        
        return results
    
    def action_log_only(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Log the threat event"""
        log_entry = {
            "timestamp": threat_event.timestamp.isoformat(),
            "anomaly_score": threat_event.anomaly_score,
            "source": threat_event.source,
            "action": "logged"
        }
        
        logger.warning(f"⚠️ Threat Logged: Score {threat_event.anomaly_score:.3f} from {threat_event.source}")
        return {"status": "logged", "entry": log_entry}
    
    async def action_alert_soc(self, threat_event: ThreatEvent, level: ResponseLevel) -> Dict[str, Any]:
        """Send alert to SOC team"""
        alert_data = {
            "timestamp": threat_event.timestamp.isoformat(),
            "anomaly_score": threat_event.anomaly_score,
            "level": level.value,
            "source": threat_event.source,
            "features": threat_event.features[:5]  # First 5 features for brevity
        }
        
        # Send email alert
        email_result = await self.send_email_alert(alert_data, level)
        
        # Send Slack alert
        slack_result = await self.send_slack_alert(alert_data, level)
        
        logger.warning(f"📢 SOC Alert Sent - Level: {level.value}, Score: {threat_event.anomaly_score:.3f}")
        
        return {
            "status": "alerted",
            "email": email_result,
            "slack": slack_result
        }
    
    def action_block_ip(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Block IP address (simulated)"""
        # This is a simulation - in practice, you'd integrate with firewall APIs
        ip_address = threat_event.ip_address or "192.168.1.100"  # Example IP
        
        logger.warning(f"🔒 IP Blocked: {ip_address}")
        
        return {
            "status": "blocked",
            "ip": ip_address,
            "action": "simulated_block"
        }
    
    def action_isolate_host(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Isolate host from network (simulated)"""
        host_id = threat_event.host_id or "HOST-001"  # Example host
        
        logger.warning(f"🖥️ Host Isolated: {host_id}")
        
        return {
            "status": "isolated",
            "host": host_id,
            "action": "simulated_isolation"
        }
    
    def action_quarantine_user(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Quarantine user account (simulated)"""
        user_id = threat_event.user_id or "USER-001"  # Example user
        
        logger.warning(f"👤 User Quarantined: {user_id}")
        
        return {
            "status": "quarantined",
            "user": user_id,
            "action": "simulated_quarantine"
        }
    
    def action_rate_limit(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Apply rate limiting (simulated)"""
        source = threat_event.source or "unknown"
        
        logger.warning(f"⏱️ Rate Limit Applied: {source}")
        
        return {
            "status": "rate_limited",
            "source": source,
            "action": "simulated_rate_limit"
        }
    
    async def action_escalate(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Escalate to senior security team"""
        escalation_data = {
            "timestamp": threat_event.timestamp.isoformat(),
            "anomaly_score": threat_event.anomaly_score,
            "source": threat_event.source,
            "severity": "critical"
        }
        
        # Send escalation alert
        await self.send_escalation_alert(escalation_data)
        
        logger.critical(f"🚨🚨 CRITICAL ESCALATION - Score: {threat_event.anomaly_score:.3f}")
        
        return {
            "status": "escalated",
            "severity": "critical",
            "action": "escalation_sent"
        }
    
    async def send_email_alert(self, alert_data: Dict[str, Any], level: ResponseLevel) -> Dict[str, Any]:
        """Send email alert (simulated)"""
        if not self.email_config:
            return {"status": "no_email_config"}
        
        try:
            # Simulate email sending
            subject = f"🚨 Security Alert - {level.value.upper()} Threat Detected"
            
            logger.info(f"📧 Email alert sent: {subject}")
            return {"status": "sent", "subject": subject}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def send_slack_alert(self, alert_data: Dict[str, Any], level: ResponseLevel) -> Dict[str, Any]:
        """Send Slack alert (simulated)"""
        if not self.slack_webhook:
            return {"status": "no_slack_config"}
        
        try:
            # Simulate Slack notification
            message = f"🚨 *{level.upper()} Security Alert* - Anomaly Score: {alert_data['anomaly_score']:.3f}"
            
            logger.info(f"💬 Slack alert sent: {message}")
            return {"status": "sent", "message": message}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def send_escalation_alert(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send escalation alert (simulated)"""
        try:
            # Simulate escalation to senior team
            logger.critical("🚨🚨 ESCALATION SENT TO SENIOR SECURITY TEAM")
            return {"status": "escalated"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def handle_batch_anomalies(self, anomaly_count: int, total_samples: int, source: str = None) -> Dict[str, Any]:
        """Handle batch of anomalies"""
        anomaly_rate = anomaly_count / total_samples
        
        logger.warning(f"📊 Batch Anomaly Detection: {anomaly_count}/{total_samples} ({anomaly_rate:.1%})")
        
        # Determine response based on anomaly rate
        if anomaly_rate > 0.5:
            level = ResponseLevel.CRITICAL
        elif anomaly_rate > 0.3:
            level = ResponseLevel.HIGH
        elif anomaly_rate > 0.1:
            level = ResponseLevel.MEDIUM
        else:
            level = ResponseLevel.LOW
        
        # Send batch alert
        await self.send_batch_alert(anomaly_count, total_samples, anomaly_rate, source, level)
        
        return {
            "status": "batch_processed",
            "anomaly_count": anomaly_count,
            "total_samples": total_samples,
            "anomaly_rate": anomaly_rate,
            "response_level": level.value
        }
    
    async def send_batch_alert(self, anomaly_count: int, total_samples: int, 
                              anomaly_rate: float, source: str, level: ResponseLevel) -> Dict[str, Any]:
        """Send batch anomaly alert"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "anomaly_count": anomaly_count,
            "total_samples": total_samples,
            "anomaly_rate": anomaly_rate,
            "source": source,
            "level": level.value
        }
        
        # Send batch alert via email and Slack
        await self.send_email_alert(alert_data, level)
        await self.send_slack_alert(alert_data, level)
        
        return {"status": "batch_alert_sent"}
    
    def log_action(self, rule: ResponseRule, threat_event: ThreatEvent, results: Dict[str, Any]) -> None:
        """Log response action"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "rule": rule.name,
            "level": rule.level.value,
            "anomaly_score": threat_event.anomaly_score,
            "source": threat_event.source,
            "actions": [action.value for action in rule.actions],
            "results": results
        }
        
        self.action_history.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-1000:]
    
    def get_action_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action history"""
        return self.action_history[-limit:]
    
    def get_response_stats(self) -> Dict[str, Any]:
        """Get response statistics"""
        if not self.action_history:
            return {"total_actions": 0}
        
        total_actions = len(self.action_history)
        actions_by_level = {}
        actions_by_type = {}
        
        for entry in self.action_history:
            level = entry.get('level', 'unknown')
            actions_by_level[level] = actions_by_level.get(level, 0) + 1
            
            for action in entry.get('actions', []):
                actions_by_type[action] = actions_by_type.get(action, 0) + 1
        
        return {
            "total_actions": total_actions,
            "actions_by_level": actions_by_level,
            "actions_by_type": actions_by_type,
            "last_action": self.action_history[-1]['timestamp'] if self.action_history else None
        }

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_response_engine():
        # Create response engine
        response_engine = ResponseEngine()
        
        # Test different anomaly levels
        test_cases = [
            (0.3, "low_threat"),
            (0.6, "medium_threat"),
            (0.8, "high_threat"),
            (0.95, "critical_threat")
        ]
        
        for score, source in test_cases:
            print(f"\nTesting anomaly score: {score}")
            
            # Handle anomaly
            result = await response_engine.handle_anomaly(
                anomaly_score=score,
                features=[1.0, 2.0, 3.0, 4.0, 5.0],
                source=source,
                ip_address="192.168.1.100",
                user_id="test_user"
            )
            
            print(f"Result: {result}")
        
        # Test batch anomalies
        batch_result = await response_engine.handle_batch_anomalies(
            anomaly_count=15,
            total_samples=50,
            source="batch_test"
        )
        
        print(f"\nBatch result: {batch_result}")
        
        # Get statistics
        stats = response_engine.get_response_stats()
        print(f"\nResponse stats: {stats}")
    
    # Run test
    asyncio.run(test_response_engine())
    print("Response engine test completed successfully!")
