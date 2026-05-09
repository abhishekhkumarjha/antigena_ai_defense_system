"""
AI Chatbot Service for Antigena Defense System
Provides intelligent assistance and task automation capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
from dataclasses import dataclass

from fastapi import HTTPException
try:
    from google import genai
    from google.genai import types
    GENAI_NEW = True
except ImportError:
    import google.generativeai as genai
    try:
        from google.generativeai import types
    except ImportError:
        types = None
    GENAI_NEW = False

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChatbotResponse:
    response: str
    actions_taken: List[str]
    confidence: float
    suggestions: List[str]
    requires_confirmation: bool

class AntigenaChatbot:
    """AI Chatbot for Antigena Defense System"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        self.genai_new = GENAI_NEW
        if not self.api_key:
            logger.warning("Google AI API key not found. Chatbot will use rule-based responses only.")
            self.client = None
        else:
            try:
                if self.genai_new:
                    self.client = genai.Client(api_key=self.api_key)
                else:
                    genai.configure(api_key=self.api_key)
                    self.client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Google AI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google AI client: {e}")
                self.client = None
        
        self.conversation_history: List[ChatMessage] = []
        self.system_context = self._build_system_context()
        
    def _build_system_context(self) -> str:
        """Build system context for the AI model"""
        return """
You are an AI assistant for the Antigena AI Defense System, a cybersecurity platform that monitors network traffic, 
detects anomalies, and automatically responds to threats. Your role is to help users understand the system, 
interpret security alerts, and automate defensive actions.

Key capabilities of Antigena:
- Real-time network traffic monitoring and anomaly detection
- Machine learning models (Isolation Forest, One-Class SVM, Autoencoder)
- Automated threat response (blocking IPs, enforcing policies)
- SHAP-based explainability for threat analysis
- Integration with network infrastructure across India

Your responsibilities:
1. Explain security events and threat levels in clear terms
2. Guide users through system features and navigation
3. Help automate security responses when appropriate
4. Provide recommendations for threat mitigation
5. Assist with system configuration and monitoring

Always prioritize security and be cautious about automated actions. 
Ask for confirmation before executing any potentially disruptive actions.
Be concise but thorough in your explanations.
"""
    
    async def process_message(self, message: str, user_context: Dict[str, Any] = None) -> ChatbotResponse:
        """Process user message and generate response"""
        
        # Add user message to conversation history
        user_message = ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.now(),
            metadata=user_context
        )
        self.conversation_history.append(user_message)
        
        # Check for automated actions
        actions_taken = []
        requires_confirmation = False
        
        # Process with AI if available
        if self.client:
            try:
                response = await self._get_ai_response(message, user_context)
                actions_taken, requires_confirmation = await self._analyze_for_actions(response, user_context)
            except Exception as e:
                logger.error(f"AI response failed: {e}")
                response = self._get_rule_based_response(message, user_context)
        else:
            response = self._get_rule_based_response(message, user_context)
        
        # Add assistant response to history
        assistant_message = ChatMessage(
            role="assistant",
            content=response,
            timestamp=datetime.now(),
            metadata={"actions_taken": actions_taken, "requires_confirmation": requires_confirmation}
        )
        self.conversation_history.append(assistant_message)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(message, response, user_context)
        
        return ChatbotResponse(
            response=response,
            actions_taken=actions_taken,
            confidence=0.8 if self.client else 0.6,
            suggestions=suggestions,
            requires_confirmation=requires_confirmation
        )
    
    async def _get_ai_response(self, message: str, user_context: Dict[str, Any] = None) -> str:
        """Get response from Google AI model"""
        
        if self.genai_new:
            # New API format
            conversation = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=self.system_context)]
                )
            ]
            
            # Add recent conversation history (last 10 messages)
            for msg in self.conversation_history[-10:]:
                conversation.append(
                    types.Content(
                        role=msg.role,
                        parts=[types.Part(text=msg.content)]
                    )
                )
            
            # Add current message
            conversation.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=message)]
                )
            )
            
            # Add context information
            if user_context:
                context_info = f"\n\nCurrent Context:\n{json.dumps(user_context, indent=2)}"
                conversation.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=context_info)]
                    )
                )
            
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model="gemini-1.5-flash",
                    contents=conversation
                )
                return response.text
            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                raise
        else:
            # Old API format
            prompt = f"{self.system_context}\n\n"
            
            # Add recent conversation history (last 10 messages)
            for msg in self.conversation_history[-10:]:
                prompt += f"{msg.role.upper()}: {msg.content}\n"
            
            # Add current message
            prompt += f"USER: {message}\n"
            
            # Add context information
            if user_context:
                prompt += f"\nCurrent Context:\n{json.dumps(user_context, indent=2)}\n"
            
            prompt += "ASSISTANT: "
            
            try:
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    prompt
                )
                return response.text
            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
                raise
    
    def _get_rule_based_response(self, message: str, user_context: Dict[str, Any] = None) -> str:
        """Get rule-based response when AI is unavailable"""
        
        message_lower = message.lower()
        
        # Help and guidance
        if any(word in message_lower for word in ['help', 'guide', 'how to', 'what is']):
            return """
I'm here to help you with the Antigena Defense System! Here's what I can assist you with:

📊 **Dashboard Navigation**: View real-time threats, network activity, and system status
🔍 **Threat Analysis**: Understand security alerts and anomaly detections
⚡ **Automation**: Help configure automated threat responses
📈 **Analytics**: Review security trends and system performance
🔧 **System Management**: Assist with configuration and troubleshooting

What would you like to know more about?
"""
        
        # Threat-related queries
        elif any(word in message_lower for word in ['threat', 'anomaly', 'alert', 'security']):
            return """
I can help you understand and respond to security threats:

🚨 **Threat Levels**: NORMAL → SUSPICIOUS → HIGH_RISK → CRITICAL
🔍 **Analysis**: Review SHAP explanations to understand why something was flagged
⚡ **Actions**: Block IPs, enforce policies, or isolate affected systems
📊 **Monitoring**: Track threat patterns and trends

Would you like me to analyze a specific threat or help you set up automated responses?
"""
        
        # System status
        elif any(word in message_lower for word in ['status', 'health', 'system', 'running']):
            return """
I can help you check system health and status:

🟢 **System Status**: Check if all components are operational
📊 **Model Performance**: Verify ML models are working correctly
🔗 **API Connectivity**: Test connections to backend services
📈 **Resource Usage**: Monitor CPU, memory, and network utilization

What specific aspect of system health would you like to check?
"""
        
        # Default response
        return """
I'm here to help with your Antigena Defense System. I can assist with:

• Understanding security alerts and threats
• Navigating the dashboard and features
• Configuring automated responses
• System monitoring and troubleshooting
• General cybersecurity guidance

Please let me know what you'd like help with, or ask me to perform a specific action!
"""
    
    async def _analyze_for_actions(self, response: str, user_context: Dict[str, Any] = None) -> tuple[List[str], bool]:
        """Analyze response for potential automated actions"""
        
        actions_taken = []
        requires_confirmation = False
        
        # Look for action indicators in the response
        response_lower = response.lower()
        
        # Check for system status requests
        if 'check system status' in response_lower or 'system health' in response_lower:
            actions_taken.append("system_status_check")
        
        # Check for threat analysis requests
        if 'analyze threat' in response_lower or 'investigate' in response_lower:
            actions_taken.append("threat_analysis")
        
        # Check for configuration changes
        if any(word in response_lower for word in ['configure', 'change setting', 'update']):
            requires_confirmation = True
        
        return actions_taken, requires_confirmation
    
    def _generate_suggestions(self, message: str, response: str, user_context: Dict[str, Any] = None) -> List[str]:
        """Generate contextual suggestions based on conversation"""
        
        suggestions = []
        message_lower = message.lower()
        
        if 'threat' in message_lower or 'alert' in message_lower:
            suggestions.extend([
                "Show me recent critical threats",
                "Explain SHAP analysis",
                "Set up automated blocking"
            ])
        
        if 'dashboard' in message_lower or 'navigate' in message_lower:
            suggestions.extend([
                "Tour the dashboard",
                "Explain threat levels",
                "Show network activity"
            ])
        
        if 'help' in message_lower:
            suggestions.extend([
                "System overview",
                "Quick start guide",
                "Common tasks"
            ])
        
        if not suggestions:
            suggestions = [
                "Check system status",
                "Review recent threats",
                "Show analytics"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def get_conversation_history(self, limit: int = 50) -> List[ChatMessage]:
        """Get conversation history"""
        return self.conversation_history[-limit:]
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    async def execute_action(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute automated action"""
        
        try:
            if action == "system_status_check":
                return await self._check_system_status()
            elif action == "threat_analysis":
                return await self._analyze_threats(params)
            elif action == "model_retraining":
                return await self._trigger_model_retraining()
            elif action == "block_suspicious_ip":
                return await self._block_suspicious_ip(params)
            elif action == "generate_security_report":
                return await self._generate_security_report()
            elif action == "check_drift_status":
                return await self._check_drift_status()
            elif action == "review_response_actions":
                return await self._review_response_actions()
            elif action == "export_anomaly_data":
                return await self._export_anomaly_data(params)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}
    
    async def _check_system_status(self) -> Dict[str, Any]:
        """Check system status by calling actual API endpoints"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Check health endpoint
                async with session.get("http://localhost:8000/health") as response:
                    health_data = await response.json()
                
                # Check metrics endpoint
                async with session.get("http://localhost:8000/metrics") as response:
                    metrics_data = await response.json()
                
                return {
                    "status": "operational" if health_data.get("status") == "healthy" else "degraded",
                    "components": {
                        "ml_models": "loaded" if health_data.get("model_loaded") else "not_loaded",
                        "api_server": "running",
                        "total_decisions": metrics_data.get("total_decisions", 0),
                        "anomaly_rate": metrics_data.get("anomaly_rate", 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error checking system status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_threats(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze recent threats using actual API data"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Get recent events
                async with session.get("http://localhost:8000/events/recent?limit=100") as response:
                    events_data = await response.json()
                
                # Get response history
                async with session.get("http://localhost:8000/response/history") as response:
                    response_data = await response.json()
                
                events = events_data.get("events", [])
                anomalies = [e for e in events if e.get("label") == "anomaly"]
                
                # Analyze patterns
                critical_threats = [e for e in anomalies if e.get("anomaly_score", 0) > 0.8]
                
                return {
                    "analysis": "Threat analysis completed",
                    "total_events": len(events),
                    "anomaly_count": len(anomalies),
                    "critical_alerts": len(critical_threats),
                    "anomaly_rate": len(anomalies) / len(events) if events else 0,
                    "avg_anomaly_score": sum(e.get("anomaly_score", 0) for e in anomalies) / len(anomalies) if anomalies else 0,
                    "response_actions": response_data.get("stats", {}).get("total_actions", 0),
                    "recommendations": self._generate_threat_recommendations(anomalies, critical_threats),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error analyzing threats: {e}")
            return {"error": str(e)}
    
    async def _trigger_model_retraining(self) -> Dict[str, Any]:
        """Trigger model retraining"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8000/models/train") as response:
                    result = await response.json()
                
                return {
                    "action": "model_retraining_triggered",
                    "status": result.get("status", "unknown"),
                    "message": result.get("message", ""),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error triggering model retraining: {e}")
            return {"error": str(e)}
    
    async def _block_suspicious_ip(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate blocking a suspicious IP"""
        ip_address = params.get("ip_address") if params else None
        
        if not ip_address:
            return {"error": "IP address required for blocking action"}
        
        # In a real implementation, this would integrate with your firewall/network infrastructure
        return {
            "action": "ip_block_simulated",
            "ip_address": ip_address,
            "status": "blocked",
            "duration": "24 hours",
            "timestamp": datetime.now().isoformat(),
            "note": "This is a simulation. In production, this would integrate with actual network security controls."
        }
    
    async def _generate_security_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security report"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Gather data from multiple endpoints
                health_resp = await session.get("http://localhost:8000/health")
                metrics_resp = await session.get("http://localhost:8000/metrics")
                events_resp = await session.get("http://localhost:8000/events/recent?limit=200")
                drift_resp = await session.get("http://localhost:8000/drift/status")
                
                health_data = await health_resp.json()
                metrics_data = await metrics_resp.json()
                events_data = await events_resp.json()
                drift_data = await drift_resp.json()
                
                report = {
                    "report_type": "security_summary",
                    "generated_at": datetime.now().isoformat(),
                    "system_health": {
                        "status": health_data.get("status"),
                        "models_loaded": health_data.get("model_loaded")
                    },
                    "performance_metrics": {
                        "total_decisions": metrics_data.get("total_decisions"),
                        "anomaly_rate": metrics_data.get("anomaly_rate"),
                        "avg_anomaly_score": metrics_data.get("avg_anomaly_score")
                    },
                    "threat_summary": {
                        "total_events": len(events_data.get("events", [])),
                        "anomalies_detected": sum(1 for e in events_data.get("events", []) if e.get("label") == "anomaly"),
                        "critical_threats": sum(1 for e in events_data.get("events", []) if e.get("anomaly_score", 0) > 0.8)
                    },
                    "drift_analysis": {
                        "status": drift_data.get("status"),
                        "drift_score": drift_data.get("drift_score"),
                        "recommendation": drift_data.get("recommendation")
                    },
                    "recommendations": self._generate_report_recommendations(metrics_data, drift_data)
                }
                
                return report
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {"error": str(e)}
    
    async def _check_drift_status(self) -> Dict[str, Any]:
        """Check model drift status"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/drift/status") as response:
                    drift_data = await response.json()
                
                return {
                    "drift_status": drift_data.get("status"),
                    "drift_score": drift_data.get("drift_score"),
                    "recommendation": drift_data.get("recommendation"),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error checking drift status: {e}")
            return {"error": str(e)}
    
    async def _review_response_actions(self) -> Dict[str, Any]:
        """Review recent response actions"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/response/history") as response:
                    response_data = await response.json()
                
                actions = response_data.get("actions", [])
                stats = response_data.get("stats", {})
                
                return {
                    "total_actions": stats.get("total_actions", 0),
                    "actions_by_level": stats.get("actions_by_level", {}),
                    "actions_by_type": stats.get("actions_by_type", {}),
                    "recent_actions": actions[:10],  # Last 10 actions
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error reviewing response actions: {e}")
            return {"error": str(e)}
    
    async def _export_anomaly_data(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export anomaly data for analysis"""
        try:
            import aiohttp
            
            limit = params.get("limit", 500) if params else 500
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/events/recent?limit={limit}") as response:
                    events_data = await response.json()
                
                events = events_data.get("events", [])
                anomalies = [e for e in events if e.get("label") == "anomaly"]
                
                return {
                    "export_type": "anomaly_data",
                    "total_events": len(events),
                    "anomaly_count": len(anomalies),
                    "data": anomalies,
                    "exported_at": datetime.now().isoformat(),
                    "format": "json"
                }
        except Exception as e:
            logger.error(f"Error exporting anomaly data: {e}")
            return {"error": str(e)}
    
    def _generate_threat_recommendations(self, anomalies: List[Dict], critical_threats: List[Dict]) -> List[str]:
        """Generate recommendations based on threat analysis"""
        recommendations = []
        
        if len(critical_threats) > 0:
            recommendations.append(f"Immediate attention required: {len(critical_threats)} critical threats detected")
        
        if len(anomalies) > 10:
            recommendations.append("High anomaly volume detected - consider reviewing detection thresholds")
        
        if len(anomalies) > 0:
            avg_score = sum(e.get("anomaly_score", 0) for e in anomalies) / len(anomalies)
            if avg_score > 0.7:
                recommendations.append("High average anomaly scores - potential security incident")
        
        recommendations.extend([
            "Review source IPs of recent anomalies for patterns",
            "Consider updating firewall rules for persistent threats",
            "Schedule regular model retraining to maintain accuracy"
        ])
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_report_recommendations(self, metrics: Dict, drift: Dict) -> List[str]:
        """Generate recommendations for security report"""
        recommendations = []
        
        if metrics.get("anomaly_rate", 0) > 0.1:
            recommendations.append("Elevated anomaly rate detected - investigate potential security incident")
        
        if drift.get("recommendation") == "trigger_retraining":
            recommendations.append("Model drift detected - schedule model retraining")
        
        if metrics.get("total_decisions", 0) < 100:
            recommendations.append("Low data volume - ensure proper data collection")
        
        recommendations.extend([
            "Regular security audits recommended",
            "Monitor response action effectiveness",
            "Update threat intelligence feeds"
        ])
        
        return recommendations
