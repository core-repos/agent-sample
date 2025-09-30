#!/bin/bash
echo "🤖 Testing Claude Agents Framework"
echo "=================================="
echo ""

if [ -d ".claude/agents" ]; then
    echo "✅ Agents directory found"
else
    echo "❌ Agents directory not found"
    exit 1
fi

AGENT_COUNT=$(ls .claude/agents/*.yml 2>/dev/null | grep -v framework.yml | grep -v index.yml | wc -l)
echo "📊 Found $AGENT_COUNT agents"
echo ""
echo "Available Agents:"
echo "-----------------"

for agent in .claude/agents/*.yml; do
    if [[ "$agent" != *"framework.yml" ]] && [[ "$agent" != *"index.yml" ]]; then
        agent_name=$(basename "$agent" .yml)
        description=$(grep "description:" "$agent" | head -1 | cut -d'"' -f2)
        echo "• $agent_name: $description"
    fi
done

echo ""
echo "Framework Configuration:"
echo "------------------------"

if [ -f ".claude/agents/framework.yml" ]; then
    echo "✅ Framework config exists"
    version=$(grep "version:" .claude/agents/framework.yml | head -1 | cut -d'"' -f2)
    echo "   Version: $version"
    project=$(grep "project:" .claude/agents/framework.yml | head -1 | cut -d'"' -f2)
    echo "   Project: $project"
else
    echo "❌ Framework config missing"
fi

echo ""
if [ -f ".claude/agents/index.yml" ]; then
    echo "✅ Agent index exists"
else
    echo "❌ Agent index missing"
fi

echo ""
if [ -f "CLAUDE.md" ]; then
    echo "✅ CLAUDE.md exists"
    if grep -q "Specialized Agents" CLAUDE.md; then
        echo "   ✅ Contains agent definitions"
    else
        echo "   ⚠️  Missing agent definitions"
    fi
else
    echo "❌ CLAUDE.md missing"
fi

echo ""
echo "=================================="
echo "✅ Agent Framework Test Complete"