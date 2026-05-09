"""
Setup script for Antigena AI Chatbot
Installs dependencies and provides configuration guidance
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing chatbot dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.3.0"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp>=3.8.0"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Setting up environment configuration...")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write("# Antigena AI Chatbot Configuration\n")
            f.write("GOOGLE_AI_API_KEY=your_google_ai_api_key_here\n")
            f.write("# Get your API key from: https://makersuite.google.com/app/apikey\n")
        
        print(f"✅ Created {env_file} file")
        print("⚠️  Please add your Google AI API key to the .env file")
        print("   Get your key from: https://makersuite.google.com/app/apikey")
    else:
        print("✅ Environment file already exists")
    
    return True

def print_usage_instructions():
    """Print usage instructions"""
    print("\n🚀 Antigena AI Chatbot Setup Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Add your Google AI API key to the .env file")
    print("2. Start the backend API server:")
    print("   cd antigena_defense/api")
    print("   python api.py")
    print("3. Start the frontend development server:")
    print("   cd ui")
    print("   npm run dev")
    print("4. Open http://localhost:3000 in your browser")
    print("5. Click the chatbot icon in the bottom-right corner")
    
    print("\n💬 Chatbot Features:")
    print("• System guidance and help")
    print("• Threat analysis and explanation")
    print("• Automated task execution")
    print("• Security report generation")
    print("• Model retraining triggers")
    print("• IP blocking simulation")
    
    print("\n🔐 Available Actions:")
    print("• system_status_check - Check system health")
    print("• threat_analysis - Analyze recent threats")
    print("• model_retraining - Trigger model retraining")
    print("• block_suspicious_ip - Block suspicious IP")
    print("• generate_security_report - Generate security report")
    print("• check_drift_status - Check model drift")
    print("• review_response_actions - Review response actions")
    print("• export_anomaly_data - Export anomaly data")
    
    print("\n⚠️  Notes:")
    print("• The chatbot works with or without the Google AI API")
    print("• Without AI API, it uses rule-based responses")
    print("• With AI API, it provides more intelligent responses")
    print("• Some actions are simulated for safety")

def main():
    """Main setup function"""
    print("🤖 Antigena AI Chatbot Setup")
    print("=" * 40)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        return
    
    # Setup environment
    if not setup_environment():
        print("❌ Setup failed during environment configuration")
        return
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main()
