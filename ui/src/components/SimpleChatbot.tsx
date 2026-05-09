/**
 * Simple Working Chatbot for Antigena Defense System
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  MessageCircle, 
  Send, 
  X, 
  Bot, 
  User, 
  Sparkles,
  Minimize2,
  Maximize2
} from 'lucide-react';
import { cn } from '../lib/utils';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface SimpleChatbotProps {
  className?: string;
}

const RULE_BASED_RESPONSES: { [key: string]: string } = {
  'help': `I'm your Antigena AI Assistant! I can provide detailed guidance on:

📊 **DASHBOARD SECTIONS**:
   • **Threat Monitor** - Real-time anomaly detection and alerts
   • **Network View** - Network traffic analysis and patterns
   • **System Monitor** - Performance metrics and health status
   • **Security Logs** - Detailed audit trails and events
   • **Analytics** - Trend analysis and reporting

🔍 **THREAT ANALYSIS**:
   • Anomaly explanation with SHAP values
   • Threat level assessment (Normal/Suspicious/High/Critical)
   • Automated response recommendations
   • Source IP and pattern analysis

⚡ **AUTOMATION CAPABILITIES**:
   • Model retraining triggers
   • IP blocking and policy enforcement
   • Security report generation
   • System health monitoring

📈 **INVESTIGATION TOOLS**:
   • Drift detection and model performance
   • Response action history
   • Export capabilities for analysis

What specific section or feature would you like detailed help with?`,
  
  'threat': `I can help you understand threat analysis in detail:

🚨 **THREAT CLASSIFICATION**:
   • **NORMAL** (0-0.3): Standard network activity
   • **SUSPICIOUS** (0.3-0.6): Unusual patterns requiring review
   • **HIGH_RISK** (0.6-0.8): Likely security incident
   • **CRITICAL** (0.8-1.0): Immediate action required

🔍 **ANALYSIS COMPONENTS**:
   • **Feature Importance**: Which network attributes triggered the alert
   • **SHAP Explanations**: Why the model flagged this as anomalous
   • **Historical Context**: How this compares to baseline behavior
   • **Risk Scoring**: Confidence levels and uncertainty

⚡ **RESPONSE ACTIONS**:
   • **IP Blocking**: Isolate suspicious network sources
   • **Policy Enforcement**: Apply security rules automatically
   • **Alert Escalation**: Notify security teams
   • **Containment**: Limit potential damage

📊 **INVESTIGATION STEPS**:
   1. Review anomaly score and contributing features
   2. Check source IP reputation and geolocation
   3. Analyze network traffic patterns
   4. Verify against known threat intelligence
   5. Determine appropriate response level

What specific aspect of threat analysis would you like to explore?`,
  
  'status': `I can provide comprehensive system status information:

🖥️ **SYSTEM COMPONENTS**:
   • **ML Models**: Isolation Forest, One-Class SVM, Autoencoder
   • **Data Pipeline**: Real-time preprocessing and feature extraction
   • **Response Engine**: Automated threat mitigation
   • **API Services**: REST endpoints for integration

📊 **HEALTH METRICS**:
   • **Model Performance**: Accuracy, precision, recall rates
   • **Processing Latency**: Real-time analysis speed
   • **Memory Usage**: Resource consumption monitoring
   • **Error Rates**: System reliability metrics

🔗 **CONNECTIVITY STATUS**:
   • **Database**: Connection to anomaly storage
   • **External APIs**: Threat intelligence feeds
   • **Network Interfaces**: Traffic monitoring points
   • **Alert Systems**: Notification channels

⚡ **OPERATIONAL CAPABILITIES**:
   • **Real-time Processing**: Sub-second anomaly detection
   • **Batch Analysis**: Historical data processing
   • **Model Retraining**: Continuous improvement
   • **Export Functions**: Data extraction for analysis

🔧 **TROUBLESHOOTING**:
   • Model loading issues and solutions
   • Data pipeline bottlenecks
   • API connectivity problems
   • Performance optimization tips

What specific system status information do you need?`,
  
  'dashboard': `I can guide you through each dashboard section in detail:

📊 **MAIN DASHBOARD - OVERVIEW**:
   • **Threat Level Indicator**: Current security posture
   • **Active Alerts**: Real-time anomaly notifications
   • **Network Activity Map**: Geographic and logical topology
   • **Quick Stats**: Total events, anomalies, response rate

🔍 **THREAT MONITOR SECTION**:
   • **Event Timeline**: Chronological security events
   • **Threat Details**: Score, source, affected systems
   • **Analysis Panel**: SHAP explanations and feature contributions
   • **Response Options**: Available mitigation actions

🌐 **NETWORK VIEW**:
   • **Traffic Flow**: Real-time network communication patterns
   • **Connection Graph**: Entity relationships and data flows
   • **Protocol Analysis**: TCP/UDP/HTTPS traffic breakdown
   • **Geographic Distribution**: Source/destination mapping

📈 **ANALYTICS DASHBOARD**:
   • **Trend Analysis**: Threat patterns over time
   • **Model Performance**: Detection accuracy metrics
   • **Response Effectiveness**: Action success rates
   • **Drift Detection**: Model degradation alerts

🔧 **SYSTEM MONITOR**:
   • **Resource Usage**: CPU, memory, disk utilization
   • **Service Health**: Component availability status
   • **Processing Queue**: Real-time analysis backlog
   • **Error Logs**: System issues and resolutions

⚙️ **NAVIGATION TIPS**:
   • Use sidebar to switch between main sections
   • Click on any event for detailed analysis
   • Use filters to focus on specific threat types
   • Export data for external analysis tools

Which dashboard section would you like detailed guidance on?`,
  
  'network': `I can help you understand network monitoring and analysis:

🌐 **NETWORK TRAFFIC ANALYSIS**:
   • **Flow Monitoring**: Real-time connection tracking
   • **Protocol Analysis**: TCP, UDP, HTTPS, SSH, SMB, DNS patterns
   • **Volume Metrics**: Bytes transferred and packet counts
   • **Session Duration**: Connection length analysis

🔍 **ANOMALY DETECTION**:
   • **Traffic Spikes**: Unusual volume increases
   • **Protocol Anomalies**: Unexpected communication patterns
   • **Geographic Oddities**: Connections from unusual locations
   • **Time-based Deviations**: Activity outside normal hours

📊 **VISUALIZATION TOOLS**:
   • **Network Graph**: Entity relationship mapping
   • **Traffic Heatmap**: Intensity visualization
   • **Protocol Distribution**: Communication type breakdown
   • **Geographic Map**: Source/destination locations

⚡ **SECURITY INVESTIGATION**:
   • **Source IP Analysis**: Reputation and geolocation lookup
   • **Destination Patterns**: Unusual target systems
   • **Port Scanning Detection**: Reconnaissance activities
   • **Data Exfiltration**: Large outbound transfers

🔧 **NETWORK SECURITY**:
   • **Firewall Integration**: Automated blocking rules
   • **IDS/IPS Coordination**: Intrusion detection systems
   • **Network Segmentation**: Isolation of compromised systems
   • **Traffic Filtering**: Malicious content blocking

What specific network analysis feature would you like to explore?`,

  'monitor': `I can explain system monitoring capabilities:

📊 **PERFORMANCE MONITORING**:
   • **CPU Usage**: Processing load and core utilization
   • **Memory Consumption**: RAM usage and allocation patterns
   • **Disk I/O**: Storage read/write operations
   • **Network Throughput**: Bandwidth utilization

🖥️ **SYSTEM HEALTH**:
   • **Service Status**: Component availability checks
   • **Response Times**: API and system latency
   • **Error Rates**: Failure frequencies and types
   • **Resource Alerts**: Threshold-based notifications

🔍 **MODEL MONITORING**:
   • **Detection Accuracy**: True positive/negative rates
   • **Processing Speed**: Real-time analysis latency
   • **Model Drift**: Performance degradation detection
   • **Feature Importance**: Key detection attributes

⚡ **AUTOMATED RESPONSES**:
   • **Threshold Alerts**: Automatic notifications
   • **System Scaling**: Resource allocation adjustments
   • **Failover Handling**: Backup system activation
   • **Recovery Actions**: Service restoration procedures

📈 **HISTORICAL ANALYSIS**:
   • **Performance Trends**: Resource usage over time
   • **Incident Patterns**: Recurring issue identification
   • **Capacity Planning**: Future resource needs
   • **Optimization Opportunities**: Efficiency improvements

What specific monitoring aspect would you like detailed information on?`,

  'logs': `I can help you understand security logging and analysis:

📋 **LOG TYPES AND SOURCES**:
   • **Security Events**: Anomaly detection results
   • **System Logs**: Application and infrastructure events
   • **Access Logs**: Authentication and authorization attempts
   • **Network Logs**: Traffic and connection records
   • **Response Actions**: Automated mitigation activities

🔍 **LOG ANALYSIS CAPABILITIES**:
   • **Pattern Recognition**: Recurring event identification
   • **Timeline Reconstruction**: Incident sequence analysis
   • **Correlation Analysis**: Cross-system event linking
   • **Statistical Summary**: Event frequencies and distributions

⚡ **SEARCH AND FILTERING**:
   • **Time Range**: Specific period analysis
   • **Threat Level**: Filter by severity
   • **Source/Destination**: Entity-based filtering
   • **Event Type**: Categorize security events
   • **Custom Queries**: Complex search criteria

📊 **VISUALIZATION TOOLS**:
   • **Timeline View**: Chronological event display
   • **Tabular Data**: Detailed log information
   • **Statistical Charts**: Event distribution graphs
   • **Export Options**: CSV, JSON, PDF formats

🔒 **SECURITY INVESTIGATION**:
   • **Incident Reconstruction**: Complete event timeline
   • **Evidence Collection**: Log preservation for forensics
   • **Compliance Reporting**: Regulatory requirement fulfillment
   • **Audit Trail**: Complete accountability record

What specific logging functionality would you like to explore?`,

  'analytics': `I can provide comprehensive analytics guidance:

📈 **THREAT ANALYTICS**:
   • **Trend Analysis**: Threat patterns over time periods
   • **Geographic Distribution**: Attack source mapping
   • **Industry Comparison**: Benchmark against similar organizations
   • **Predictive Analytics**: Future threat forecasting
   • **Seasonal Patterns**: Time-based attack variations

🎯 **PERFORMANCE METRICS**:
   • **Detection Accuracy**: Model precision and recall rates
   • **False Positive Analysis**: Alert accuracy optimization
   • **Response Time**: Mean time to detection and response
   • **Throughput Analysis**: Events processed per second
   • **Resource Efficiency**: CPU/memory per detection

📊 **BUSINESS INTELLIGENCE**:
   • **Risk Scoring**: Quantified threat assessment
   • **Impact Analysis**: Business disruption potential
   • **ROI Metrics**: Security investment effectiveness
   • **Compliance Status**: Regulatory adherence tracking
   • **Cost Analysis**: Security operations expenditure

🔍 **ADVANCED ANALYTICS**:
   • **Machine Learning Insights**: Model behavior analysis
   • **Behavioral Baselines**: Normal activity patterns
   • **Anomaly Clustering**: Grouping similar threats
   • **Root Cause Analysis**: Underlying vulnerability identification
   • **Threat Intelligence Integration**: External data correlation

⚡ **REPORTING CAPABILITIES**:
   • **Executive Summaries**: High-level security posture
   • **Technical Reports**: Detailed analysis findings
   • **Compliance Reports**: Regulatory requirement documentation
   • **Custom Dashboards**: Tailored analytics views
   • **Automated Alerts**: Threshold-based notifications

What specific analytics capability would you like detailed guidance on?`,
  
  'model': `I can explain the machine learning models in detail:

🤖 **ENSEMBLE ARCHITECTURE**:
   • **Isolation Forest**: Unsupervised anomaly detection
   • **One-Class SVM**: Boundary-based classification
   • **Autoencoder**: Reconstruction error detection
   • **Ensemble Method**: Weighted voting system
   • **Confidence Scoring**: Probability-based assessment

📊 **MODEL TRAINING**:
   • **Feature Engineering**: 42-dimensional feature space
   • **Data Preprocessing**: Normalization and scaling
   • **Cross-Validation**: Performance optimization
   • **Hyperparameter Tuning**: Model configuration optimization
   • **Ensemble Weights**: Optimal model combination

🔍 **DETECTION MECHANISMS**:
   • **Statistical Anomalies**: Deviation from normal patterns
   • **Behavioral Analysis**: Historical pattern comparison
   • **Reconstruction Error**: Autoencoder-based detection
   • **Boundary Detection**: SVM classification boundaries
   • **Ensemble Voting**: Multiple model consensus

⚡ **MODEL PERFORMANCE**:
   • **Accuracy Metrics**: True positive/negative rates
   • **ROC Curves**: Threshold optimization analysis
   • **Precision-Recall**: Trade-off analysis
   • **F1 Score**: Balanced performance measure
   • **Calibration**: Probability accuracy assessment

🔧 **MODEL OPERATIONS**:
   • **Real-time Inference**: Sub-second prediction latency
   • **Batch Processing**: Historical data analysis
   • **Model Retraining**: Continuous improvement cycles
   • **Drift Detection**: Performance degradation monitoring
   • **A/B Testing**: Model comparison frameworks

What specific model aspect would you like to explore?`,
  
  'api': `I can explain the API and integration capabilities:

🔗 **REST API ENDPOINTS**:
   • **POST /predict**: Single sample anomaly detection
   • **POST /predict/batch**: Multiple sample analysis
   • **POST /ingest/telemetry**: Raw data processing
   • **GET /health**: System status check
   • **GET /models/info**: Model information
   • **POST /models/train**: Retraining trigger

📊 **DATA FORMATS**:
   • **Input**: JSON with feature vectors and metadata
   • **Output**: Anomaly scores and explanations
   • **Batch**: Arrays of feature vectors
   • **Telemetry**: Raw network event data
   • **Response**: Standardized result format

⚡ **INTEGRATION CAPABILITIES**:
   • **Real-time Processing**: Streaming data analysis
   • **Webhook Support**: Automated alert delivery
   • **CORS Configuration**: Cross-origin requests
   • **Authentication**: API key security
   • **Rate Limiting**: Request throttling

🔧 **DEVELOPMENT TOOLS**:
   • **OpenAPI Specification**: Complete API documentation
   • **Interactive Docs**: Swagger UI testing
   • **SDK Support**: Multiple language libraries
   • **Webhook Testing**: Endpoint validation
   • **Error Handling**: Comprehensive error responses

📈 **MONITORING ENDPOINTS**:
   • **GET /metrics**: System performance data
   • **GET /events/recent**: Recent decision history
   • **GET /drift/status**: Model degradation alerts
   • **GET /response/history**: Action audit trail
   • **GET /security/policy**: Configuration review

What specific API functionality would you like to explore?`,
  
  'response': `I can explain automated response capabilities:

⚡ **RESPONSE ENGINE ARCHITECTURE**:
   • **Rule-based System**: Configurable response policies
   • **Threat Level Mapping**: Score-based action selection
   • **Multi-channel Alerts**: Email, Slack, webhook notifications
   • **Action Queuing**: Prioritized response execution
   • **Audit Logging**: Complete action history

🚨 **AUTOMATED ACTIONS**:
   • **IP Blocking**: Firewall rule integration
   • **Policy Enforcement**: Security rule application
   • **User Notification**: Alert delivery systems
   • **System Isolation**: Containment procedures
   • **Evidence Collection**: Forensic data preservation

📊 **RESPONSE POLICIES**:
   • **Threshold-based**: Score-triggered actions
   • **Time-based**: Automated scheduling
   • **Entity-specific**: Targeted response rules
   • **Geographic Rules**: Location-based policies
   • **Compliance-driven**: Regulatory requirement actions

🔍 **INVESTIGATION WORKFLOW**:
   • **Alert Triage**: Severity assessment and prioritization
   • **Context Gathering**: System state and event correlation
   • **Response Planning**: Action selection and approval
   • **Execution**: Automated or manual response implementation
   • **Verification**: Action effectiveness confirmation

⚙️ **CONFIGURATION MANAGEMENT**:
   • **Policy Editor**: Visual rule creation interface
   • **Action Templates**: Predefined response procedures
   • **Approval Workflows**: Multi-level authorization
   • **Testing Framework**: Simulation and validation
   • **Rollback Capabilities**: Action reversal procedures

📈 **PERFORMANCE METRICS**:
   • **Response Time**: Mean time to action execution
   • **Success Rate**: Action effectiveness measurement
   • **False Positive Rate**: Unnecessary action tracking
   • **Coverage Analysis**: Threat handling completeness
   • **Resource Impact**: System overhead measurement

What specific response capability would you like to explore?`,
  
  'default': `I'm your Antigena AI Assistant! I can provide detailed guidance on any aspect of the system:

📚 **AVAILABLE TOPICS**:
   • **Dashboard Navigation** - All sections and features
   • **Threat Analysis** - Anomaly detection and investigation
   • **Network Monitoring** - Traffic analysis and patterns
   • **System Status** - Health and performance metrics
   • **Analytics** - Trend analysis and reporting
   • **Security Logs** - Audit trails and investigation
   • **ML Models** - Detection algorithms and performance
   • **API Integration** - Endpoints and development
   • **Response Actions** - Automation and workflows
   • **Configuration** - System setup and optimization

🎯 **HOW TO GET HELP**:
   • Ask about specific sections: "dashboard", "threats", "network", "monitor", "logs", "analytics", "models", "api", "response"
   • Request specific functionality: "How do I analyze threats?", "Explain model performance"
   • Get troubleshooting help: "System errors", "Model training issues"
   • Request automation: "Set up alerts", "Configure responses"

💡 **EXAMPLE QUESTIONS**:
   • "Explain the threat analysis process"
   • "How do I interpret SHAP values?"
   • "What are the different threat levels?"
   • "How do I set up automated responses?"
   • "Show me network monitoring features"
   • "Explain the ML models in detail"

What specific aspect of Antigena would you like detailed help with?`
};

export default function SimpleChatbot({ className }: SimpleChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, isMinimized]);

  const getRuleBasedResponse = (message: string): string => {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('help')) return RULE_BASED_RESPONSES.help;
    if (lowerMessage.includes('threat') || lowerMessage.includes('alert') || lowerMessage.includes('anomaly')) {
      return RULE_BASED_RESPONSES.threat;
    }
    if (lowerMessage.includes('status') || lowerMessage.includes('health')) return RULE_BASED_RESPONSES.status;
    if (lowerMessage.includes('dashboard') || lowerMessage.includes('navigate')) return RULE_BASED_RESPONSES.dashboard;
    
    return RULE_BASED_RESPONSES.default;
  };

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate processing time
    setTimeout(() => {
      const response = getRuleBasedResponse(message);
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  if (!isOpen) {
    return (
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={cn("fixed bottom-6 right-6 z-50", className)}
      >
        <button
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110 group"
        >
          <MessageCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full animate-pulse" />
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={cn("fixed bottom-6 right-6 w-96 h-[600px] bg-[#080808] border border-white/10 rounded-2xl shadow-2xl z-50 flex flex-col", className)}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-indigo-600/10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-sm">Antigena AI Assistant</h3>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-[10px] text-emerald-400">Online</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          >
            {isMinimized ? <Maximize2 className="w-4 h-4 text-slate-400" /> : <Minimize2 className="w-4 h-4 text-slate-400" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={cn(
                    "flex gap-3",
                    message.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 bg-indigo-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-indigo-400" />
                    </div>
                  )}
                  
                  <div className={cn(
                    "max-w-[80%] rounded-lg p-3",
                    message.role === 'user' 
                      ? "bg-indigo-600/20 text-white ml-auto" 
                      : "bg-white/5 text-slate-300"
                  )}>
                    <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>
                    <div className="mt-1 text-[10px] text-slate-500">
                      {message.timestamp}
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                </motion.div>
              ))}

              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3 justify-start"
                >
                  <div className="w-8 h-8 bg-indigo-600/20 rounded-lg flex items-center justify-center">
                    <Bot className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/10">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about Antigena..."
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-colors"
              />
              <button
                onClick={() => sendMessage(inputValue)}
                disabled={!inputValue.trim() || isTyping}
                className="p-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-700 disabled:opacity-50 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
}
