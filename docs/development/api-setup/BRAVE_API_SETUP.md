# Brave Search API Setup Guide

**Purpose**: Get your FREE Brave Search API key for enhanced guild development  
**Benefit**: Access to recent solutions, GitHub issues, and Stack Overflow discussions  
**Cost**: FREE (2,000 queries/month)  

---

## 🔍 Step-by-Step Setup

### **1. Register for Brave Search API**
- **Visit**: https://brave.com/search/api/
- **Click**: "Get API Key" button
- **Register**: Create account or sign in

### **2. Choose FREE Tier**
- **Select**: Free tier (2,000 queries/month)
- **Perfect for**: Personal development and guild-based parallel development
- **No credit card required** for free tier

### **3. Get Your API Key**
- **Login**: to your Brave API dashboard
- **Navigate**: to API Keys section
- **Click**: "Add API Key"
- **Name**: your key (e.g., "Guild Development")
- **Copy**: the generated API key

### **4. Configure MCP Server**
```bash
# Set your API key (replace with your actual key)
export BRAVE_API_KEY='your_actual_api_key_here'

# Add Brave Search MCP server
claude mcp add brave-search -s user -- env BRAVE_API_KEY="$BRAVE_API_KEY" npx -y @modelcontextprotocol/server-brave-search

# Or re-run our setup script with the API key
./setup-enhanced-guilds.sh
```

---

## 🎯 What You Get with Brave Search

### **Recent Solutions**
- Latest GitHub issues and solutions
- Current Stack Overflow discussions
- Recent blog posts on implementation patterns

### **Guild-Specific Benefits**
- **Infrastructure**: Latest K8s operator patterns and solutions
- **Security**: Recent security vulnerabilities and mitigations
- **AI/LLM**: Current LLM performance studies and optimizations
- **Observability**: Recent monitoring platform updates and cost strategies

### **Enhanced Commands**
Once configured, you can use:
```bash
/user:k8s-research "Kubernetes operator health monitoring 2024"
/user:security-research "JWT RS256 implementation best practices"
/user:llm-research "Multi-provider LLM failover patterns"
/user:monitoring-research "AWS CloudWatch cost optimization strategies"
```

---

## 🚀 Verification

After setup, verify your configuration:
```bash
# Check MCP servers
claude mcp list

# Should show both:
# context7: https://mcp.context7.com/sse (SSE)
# brave-search: ... (with your configuration)
```

---

## 🎯 Ready for Enhanced Development

Once Brave Search is configured, you'll have:
- ✅ **Context7**: Current documentation for all technologies
- ✅ **Brave Search**: Recent solutions and implementation examples
- ✅ **Custom Commands**: 10 guild-specific workflow commands
- ✅ **Subagents**: Parallel research capabilities

**Enhanced parallel development across all 4 guilds ready!** 🚀

---

## 💡 Optional: Alternative Setup

If you prefer not to use Brave Search API, you can still proceed with:
- ✅ **Context7 MCP**: Current documentation access
- ✅ **Custom Commands**: Streamlined workflows
- ✅ **Built-in Web Search**: Claude Code's native web search capabilities

The enhanced guild development will still provide significant benefits over basic parallel development.